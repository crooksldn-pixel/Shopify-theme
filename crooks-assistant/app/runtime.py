"""The composition root: one place where every component is constructed and wired together."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.clients.gmail import GmailClient
from app.clients.shopify import ShopifyClient
from app.clients.whisper import WhisperClient
from app.kb.loader import KnowledgeBase, build_system_prompt, load
from app.logging.turnlog import TurnLog
from app.providers.base import ClaudeProvider
from app.providers.max_agent_sdk import MaxAgentSDKProvider
from app.session.manager import SessionManager, get_manager
from app.speech.normalise import Catalogue, Normaliser, from_file
from app.speech.transcribe import Transcriber
from config.settings import Settings, get_settings

log = logging.getLogger("crooks.runtime")

CATALOGUE_TTL_S = 3600  # M7: refresh the live product catalogue hourly


@dataclass
class Runtime:
    settings: Settings
    sessions: SessionManager
    whisper: WhisperClient
    normaliser: Normaliser
    transcriber: Transcriber
    shopify: ShopifyClient
    gmail: GmailClient
    provider: ClaudeProvider
    kb: KnowledgeBase
    turnlog: TurnLog
    started_at: float = field(default_factory=time.time)
    _catalogue_refreshed_at: float = 0.0

    @property
    def uptime_s(self) -> float:
        return time.time() - self.started_at

    async def maybe_refresh_catalogue(self) -> None:
        """Repoint the normaliser at the live Shopify catalogue, hourly, cached to disk.

        Failure here is not fatal: the seed terminology file keeps working, which is the whole
        reason M3 built against a file rather than waiting for M7.
        """
        if time.time() - self._catalogue_refreshed_at < CATALOGUE_TTL_S:
            return
        self._catalogue_refreshed_at = time.time()
        try:
            from app.tools.shopify_tools import catalogue_terms

            live = await catalogue_terms()
        except Exception as exc:  # noqa: BLE001
            log.warning("live catalogue unavailable, keeping the seed list: %s", exc)
            return
        if not live:
            return
        seed = list(self.normaliser.catalogue.terms)
        cache = self.settings.kb_dir / ".catalogue-cache.txt"
        try:
            cache.write_text("\n".join(live), encoding="utf-8")
        except OSError:
            pass
        merged = seed + live
        self.normaliser._source = lambda: Catalogue(merged)  # noqa: SLF001 — same interface
        self.normaliser.refresh()
        log.info("normaliser repointed at live catalogue: %d terms", len(merged))

    def reload_kb(self) -> KnowledgeBase:
        self.kb = load(self.settings.kb_dir)
        return self.kb


def build(settings: Settings | None = None) -> Runtime:
    settings = settings or get_settings()
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    settings.bench_audio_dir.mkdir(parents=True, exist_ok=True)

    sessions = get_manager(settings.session_idle_timeout_s)
    whisper = WhisperClient(settings.whisper_url, model=settings.whisper_model)
    normaliser = _build_normaliser(settings)
    transcriber = Transcriber(
        whisper,
        normaliser,
        save_dir=settings.bench_audio_dir if settings.save_captures else None,
    )

    shopify = ShopifyClient(
        settings.shopify_shop_domain,
        settings.shopify_api_version,
        auth_mode=settings.shopify_auth_mode,
    )
    gmail = GmailClient()

    # Register the tool modules. Importing them is what runs the @tool decorators.
    from app.tools import gmail_tools, mock, shopify_tools  # noqa: F401

    shopify_tools.bind(shopify)
    gmail_tools.bind(gmail, customer_lookup=_make_customer_lookup(shopify))

    kb = load(settings.kb_dir)
    provider = MaxAgentSDKProvider(
        system_prompt=build_system_prompt(kb),
        model=settings.claude_model,
        session_lookup=sessions.get_or_create,
        tool_timeout_s=settings.tool_timeout_s,
        cli_path=settings.claude_cli_path,
    )

    return Runtime(
        settings=settings,
        sessions=sessions,
        whisper=whisper,
        normaliser=normaliser,
        transcriber=transcriber,
        shopify=shopify,
        gmail=gmail,
        provider=provider,
        kb=kb,
        turnlog=TurnLog(settings.log_dir),
    )


def _build_normaliser(settings: Settings) -> Normaliser:
    seed = settings.kb_dir / "terminology.md"
    normaliser = from_file(seed)
    cache = settings.kb_dir / ".catalogue-cache.txt"
    if cache.exists():
        # A warm start uses last hour's live catalogue rather than falling back to the seed.
        try:
            cached = [t for t in cache.read_text(encoding="utf-8").splitlines() if t.strip()]
            terms = list(normaliser.catalogue.terms) + cached
            normaliser = Normaliser(lambda: Catalogue(terms))
        except OSError:
            pass
    return normaliser


def _make_customer_lookup(shopify: ShopifyClient):
    """Cross-reference an email sender against Shopify customers, cached per process.

    Gmail must keep working when Shopify does not, so a failure here returns None ("could not
    check"), never False ("not a customer") — those are different answers.
    """
    cache: dict[str, bool] = {}

    async def lookup(email: str) -> bool | None:
        email = (email or "").strip().lower()
        if not email:
            return None
        if email in cache:
            return cache[email]
        from app.tools.shopify_tools import _search_customers

        matches = await _search_customers(shopify, f"email:{email}", limit=1)
        cache[email] = bool(matches)
        return cache[email]

    return lookup


def seed_paths(settings: Settings) -> list[Path]:
    return [settings.kb_dir, settings.bench_audio_dir, settings.log_dir]
