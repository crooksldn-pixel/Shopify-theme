"""GET /media/shopify/{sig}/{w}?u=… — one image, from Shopify's CDN, through the Mac.

Bounded in every direction: the signature is checked before any request leaves; only an
image comes back; only this many bytes of it; only for this long; and a copy is kept on disk
so the same thumbnail is not fetched for every look at the same order.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from pathlib import Path

import httpx
from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from app import media

log = logging.getLogger("crooks.media")

router = APIRouter(prefix="/media")

MAX_BYTES = 2_000_000
TIMEOUT_S = 4.0
CONCURRENCY = 4
CACHE_MAX_BYTES = 50_000_000
CACHE_CONTROL = "private, max-age=86400"
_IMAGE_TYPES = ("image/jpeg", "image/png", "image/webp", "image/gif", "image/avif")
# An image is bytes to draw and nothing else: never sniffed into a document, never a page.
_HEADERS = {"Cache-Control": CACHE_CONTROL, "X-Content-Type-Options": "nosniff", "Content-Security-Policy": "default-src 'none'; sandbox"}
# The sweep reads every cached file's size; it runs off the loop, and not on every write.
SWEEP_EVERY = 20
_writes = 0

_semaphore: asyncio.Semaphore | None = None
_http: httpx.AsyncClient | None = None


def _client() -> httpx.AsyncClient:
    global _http
    if _http is None or _http.is_closed:
        _http = httpx.AsyncClient(timeout=TIMEOUT_S, follow_redirects=False, headers={"User-Agent": "CROOKS-Assistant/1.0"})
    return _http


async def aclose() -> None:
    global _http
    if _http is not None and not _http.is_closed:
        await _http.aclose()
    _http = None


def _gate() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(CONCURRENCY)
    return _semaphore


@router.get("/shopify/{sig}/{width}")
async def shopify_image(request: Request, sig: str, width: int, u: str = Query(default="")) -> Response:
    if not media.verify(sig, width, u):
        # Not a path a card was built with. Nothing is fetched and nothing is said about why.
        return Response(status_code=404)
    cache_dir = _cache_dir(request)
    key = hashlib.sha256(f"{width}\n{u}".encode()).hexdigest()
    cached = _read_cache(cache_dir, key)
    if cached is not None:
        body, media_type = cached
        return Response(content=body, media_type=media_type, headers={**_HEADERS, "X-Crooks-Cache": "hit"})
    async with _gate():
        try:
            # One deadline for the whole fetch: a CDN that drips bytes cannot hold a slot.
            body, media_type = await asyncio.wait_for(_fetch(media.sized(u, width)), timeout=TIMEOUT_S)
        except _Refused as exc:
            log.info("image refused: %s", exc)
            return Response(status_code=502)
        except (httpx.HTTPError, TimeoutError) as exc:
            log.info("image fetch failed: %s", type(exc).__name__)
            return Response(status_code=502)
    await _write_cache(cache_dir, key, body, media_type)
    return Response(content=body, media_type=media_type, headers={**_HEADERS, "X-Crooks-Cache": "miss"})


class _Refused(RuntimeError):
    pass


async def _fetch(url: str) -> tuple[bytes, str]:
    """The bytes of one image, or a refusal: not a 200, not an image, or more than allowed.
    Redirects are not followed — the signed URL is the one that is fetched, or nothing is."""
    async with _client().stream("GET", url) as response:
        if response.status_code != 200:
            raise _Refused(f"status {response.status_code}")
        media_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
        if media_type not in _IMAGE_TYPES:
            raise _Refused(f"not an image ({media_type or 'no type'})")
        declared = response.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > MAX_BYTES:
            raise _Refused("too large")
        chunks: list[bytes] = []
        total = 0
        async for chunk in response.aiter_bytes():
            total += len(chunk)
            if total > MAX_BYTES:
                raise _Refused("too large")
            chunks.append(chunk)
    body = b"".join(chunks)
    if not _looks_like_image(body):
        raise _Refused("not an image (bytes)")
    return body, media_type


def _looks_like_image(body: bytes) -> bool:
    head = body[:16]
    return (
        head.startswith(b"\xff\xd8\xff")             # JPEG
        or head.startswith(b"\x89PNG\r\n\x1a\n")      # PNG
        or head.startswith(b"GIF8")                   # GIF
        or (head[:4] == b"RIFF" and head[8:12] == b"WEBP")
        or head[4:12] in (b"ftypavif", b"ftypavis")   # AVIF
    )


# ---------------------------------------------------------------- the disk cache


def _cache_dir(request: Request) -> Path:
    settings = request.app.state.runtime.settings
    path = Path(settings.media_cache_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_cache(cache_dir: Path, key: str) -> tuple[bytes, str] | None:
    body_path = cache_dir / f"{key}.img"
    type_path = cache_dir / f"{key}.type"
    try:
        if not body_path.exists() or not type_path.exists():
            return None
        body = body_path.read_bytes()
        media_type = type_path.read_text(encoding="ascii").strip()
        if media_type not in _IMAGE_TYPES or not body:
            return None
        body_path.touch()   # recently used: the sweep drops the oldest first
        return body, media_type
    except OSError:
        return None


async def _write_cache(cache_dir: Path, key: str, body: bytes, media_type: str) -> None:
    global _writes
    try:
        (cache_dir / f"{key}.img").write_bytes(body)
        (cache_dir / f"{key}.type").write_text(media_type, encoding="ascii")
    except OSError as exc:
        log.debug("image cache write failed: %s", exc)
        return
    _writes += 1
    if _writes % SWEEP_EVERY == 0:
        try:
            await asyncio.to_thread(_sweep, cache_dir)
        except OSError as exc:
            log.debug("image cache sweep failed: %s", exc)


def _sweep(cache_dir: Path) -> None:
    """Keep the cache under its bound by dropping the least recently used images."""
    files = sorted(cache_dir.glob("*.img"), key=lambda p: p.stat().st_mtime)
    total = sum(p.stat().st_size for p in files)
    for path in files:
        if total <= CACHE_MAX_BYTES:
            break
        size = path.stat().st_size
        path.unlink(missing_ok=True)
        path.with_suffix(".type").unlink(missing_ok=True)
        total -= size
