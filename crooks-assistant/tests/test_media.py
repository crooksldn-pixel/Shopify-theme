"""The image path: a card carries only a path the Mac signed; the route serves only Shopify's
CDN, only images, only so many bytes; nothing else is ever fetched."""

from __future__ import annotations

import httpx
import pytest

from app import media
from app.routes import media as media_route

CDN = "https://cdn.shopify.com/s/files/1/0001/products/yard-jeans.jpg?v=1"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


@pytest.mark.parametrize("url", [
    CDN, "https://shop.shopifycdn.com/s/x.png", "https://cdn.shopify.com/a.webp",
])
def test_shopify_cdn_urls_are_signed_into_same_origin_paths(url):
    path = media.signed_path(url)
    assert path.startswith("/media/shopify/") and "/160?u=" in path
    sig = path.split("/")[3]
    assert media.verify(sig, 160, url) and not media.verify(sig, 320, url) and not media.verify(sig[::-1], 160, url)


@pytest.mark.parametrize("url", [
    "http://cdn.shopify.com/a.jpg", "https://cdn.shopify.com.evil.example/a.jpg", "https://evil.example/cdn.shopify.com/a.jpg",
    "https://127.0.0.1/a.jpg", "https://user:pw@cdn.shopify.com/a.jpg", "https://cdn.shopify.com:8443/a.jpg",
    "file:///etc/passwd", "", None, 42, "https://cdn.shopify.com/" + "a" * 700,
])
def test_anything_else_is_not_signed_and_never_verifies(url):
    assert media.signed_path(url) is None
    assert media.verify(media.signature(str(url), 160), 160, str(url)) is False


def test_only_the_listed_widths_are_signed():
    assert "/999?u=" not in media.signed_path(CDN, 999) and "/160?u=" in media.signed_path(CDN, 999)
    assert "/640?u=" in media.signed_path(CDN, 640)


def test_the_cdn_is_asked_for_the_small_size():
    assert media.sized(CDN, 160).endswith("?v=1&width=160")
    assert media.sized("https://cdn.shopify.com/a.jpg", 320).endswith("a.jpg?width=320")


class Upstream(httpx.AsyncBaseTransport):
    def __init__(self, *, status=200, body=PNG, content_type="image/png", headers=None) -> None:
        self.status, self.body, self.content_type, self.extra = status, body, content_type, headers or {}
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request):
        self.requests.append(request)
        headers = {"content-type": self.content_type, **self.extra}
        return httpx.Response(self.status, headers=headers, content=self.body)


@pytest.fixture()
async def client(monkeypatch, tmp_path):
    from app.clients.elevenlabs import ScribeClient
    from app.clients.elevenlabs_tts import VoiceClient
    from app.main import app
    from app.providers import max_agent_sdk

    async def no_start(self):
        raise RuntimeError("tests never start the real Claude provider")

    monkeypatch.setattr(max_agent_sdk.MaxAgentSDKProvider, "start", no_start)

    async def fake_scribe_health(self):
        return True, "fake scribe"

    monkeypatch.setattr(ScribeClient, "health", fake_scribe_health)
    monkeypatch.setattr(VoiceClient, "health", lambda self: (True, "fake voice"))
    async with app.router.lifespan_context(app):
        runtime = app.state.runtime
        runtime.settings = runtime.settings.model_copy(update={"media_cache_dir": tmp_path / "media"})
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            c.runtime = runtime
            yield c
    await media_route.aclose()


def upstream(monkeypatch, **kwargs) -> Upstream:
    transport = Upstream(**kwargs)
    monkeypatch.setattr(media_route, "_http", httpx.AsyncClient(transport=transport, follow_redirects=False))
    return transport


async def test_a_signed_path_serves_the_image_and_caches_it(client, monkeypatch):
    up = upstream(monkeypatch)
    path = media.signed_path(CDN)
    first = await client.get(path)
    assert first.status_code == 200 and first.headers["content-type"] == "image/png" and first.content == PNG
    assert first.headers["cache-control"] == "private, max-age=86400" and first.headers["x-crooks-cache"] == "miss"
    assert str(up.requests[0].url).endswith("&width=160")
    second = await client.get(path)
    assert second.status_code == 200 and second.headers["x-crooks-cache"] == "hit" and len(up.requests) == 1


async def test_an_unsigned_or_altered_path_fetches_nothing(client, monkeypatch):
    up = upstream(monkeypatch)
    path = media.signed_path(CDN)
    assert (await client.get(path.replace("/160?", "/320?"))).status_code == 404
    assert (await client.get(path.replace("u=https", "u=http"))).status_code == 404
    assert (await client.get("/media/shopify/deadbeef/160?u=https%3A%2F%2Fevil.example%2Fa.jpg")).status_code == 404
    assert (await client.get("/media/shopify/deadbeef/160?u=" + CDN.replace("https://", "https%3A%2F%2F"))).status_code == 404
    assert up.requests == []


async def test_a_response_that_is_not_an_image_is_refused(client, monkeypatch):
    upstream(monkeypatch, content_type="text/html", body=b"<html>")
    assert (await client.get(media.signed_path(CDN))).status_code == 502
    upstream(monkeypatch, content_type="image/png", body=b"<html>not really</html>")
    assert (await client.get(media.signed_path(CDN))).status_code == 502
    upstream(monkeypatch, status=302, headers={"location": "https://evil.example/x.png"})
    assert (await client.get(media.signed_path(CDN))).status_code == 502


async def test_an_oversized_image_is_refused(client, monkeypatch):
    upstream(monkeypatch, body=JPEG + b"\x00" * (media_route.MAX_BYTES + 10), content_type="image/jpeg")
    assert (await client.get(media.signed_path(CDN))).status_code == 502
    upstream(monkeypatch, body=JPEG, content_type="image/jpeg", headers={"content-length": str(media_route.MAX_BYTES + 1)})
    assert (await client.get(media.signed_path(CDN))).status_code == 502


def test_the_service_worker_never_keeps_media():
    from pathlib import Path

    source = Path("web/sw.js").read_text(encoding="utf-8")
    assert "/media/" not in source
