"""The composition root: one place where every component is constructed and wired together."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.actions.engine import ActionEngine
from app.actions.engine import install as install_engine
from app.actions.ledger import ActionLedger
from app.clients.elevenlabs import ScribeClient
from app.clients.elevenlabs_tts import VoiceClient
from app.clients.gmail import GmailClient
from app.clients.shopify import ShopifyClient
from app.clients.whisper import WhisperClient
from app.kb.loader import KnowledgeBase, build_system_prompt, load
from app.logging.turnlog import TurnLog
from app.providers.base import ClaudeProvider
from app.providers.max_agent_sdk import MaxAgentSDKProvider
from app.session.manager import SessionManager, get_manager
from app.speech.normalise import Normaliser, from_file
from app.speech.transcribe import Transcriber
from config.settings import Settings, get_settings

log = logging.getLogger("crooks.runtime")

CATALOGUE_TTL_S = 3600  # M7: refresh the live product catalogue hourly


@dataclass
class Runtime:
    settings: Settings
    sessions: SessionManager
    whisper: WhisperClient
    scribe: ScribeClient
    voice: VoiceClient
    normaliser: Normaliser
    transcriber: Transcriber
    shopify: ShopifyClient
    gmail: GmailClient
    provider: ClaudeProvider
    kb: KnowledgeBase
    turnlog: TurnLog
    actions: ActionEngine
    started_at: float = field(default_factory=time.time)
    build: str = ""
    _catalogue_refreshed_at: float = 0.0
    _catalogue_task: asyncio.Task | None = None

    @property
    def uptime_s(self) -> float:
        return time.time() - self.started_at

    def refresh_catalogue_soon(self) -> None:
        """Kick the hourly catalogue refresh off beside the current turn rather than in front
        of it. A turn never waits on Shopify for a list it does not need to answer."""
        if time.time() - self._catalogue_refreshed_at < CATALOGUE_TTL_S:
            return
        if self._catalogue_task is not None and not self._catalogue_task.done():
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        self._catalogue_task = loop.create_task(self.maybe_refresh_catalogue())

    async def aclose(self) -> None:
        """Release what the process holds open: the provider's subprocesses and every kept
        HTTPS connection."""
        if self._catalogue_task is not None and not self._catalogue_task.done():
            self._catalogue_task.cancel()
        await self.provider.stop()
        for client in (self.voice, self.scribe, self.whisper, self.shopify):
            close = getattr(client, "aclose", None)
            if close is not None:
                try:
                    await close()
                except Exception:  # noqa: BLE001 — shutting down; nothing to do about it
                    log.debug("closing %s failed", type(client).__name__, exc_info=True)

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
            # Products only. Customer names are personal data and do not belong in a file.
            cache.write_text("\n".join(t for t in live if t in set(live[: live_product_count(live)])), encoding="utf-8")
        except OSError:
            pass
        # Live terms first, hand-written seed (with its aliases) LAST: the Whisper prompt is
        # truncated from the front, so the terms the owner wrote must be the ones that survive.
        merged = live + seed
        # Everything after the boundary is a person. Those names still correct transcripts on
        # this Mac; they are held back from the Scribe keyterms, which leave it.
        # `seed` carries last hour's terms forward, so the names already marked personal are
        # carried forward with them — a name is never quietly un-marked by the next refresh.
        # (Catalogue stores personal entries in comparison form; cleaning them twice is a no-op.)
        customers = live[live_product_count(live) + 1 :] + list(self.normaliser.catalogue.personal)
        self.normaliser.repoint(
            merged, aliases=self.normaliser.catalogue.aliases, personal=customers
        )
        log.info("normaliser repointed at live catalogue: %d terms", len(merged))

    def reload_kb(self) -> KnowledgeBase:
        self.kb = load(self.settings.kb_dir)
        return self.kb

    def system_prompt(self) -> str:
        return build_system_prompt(self.kb, writes_enabled=self.settings.writes_enabled)

    @property
    def allowed_logins(self) -> tuple[str, ...]:
        return tuple(
            login.strip().lower() for login in self.settings.allowed_logins.split(",") if login.strip()
        )

    async def write_status(self, operation: str | None = None) -> WriteStatus:
        """Can a proposal execute here, now? Deterministic and read-only: configuration, the
        allow-list, and the scopes the store has granted (a query, cached). Never a mutation.
        With an operation, only that change's own scope counts: a fulfilment scope the store
        has not granted does not stop a note."""
        settings = self.settings
        if not settings.writes_enabled:
            return WriteStatus("disabled", "disabled — CROOKS_WRITES_ENABLED=false")
        if not self.allowed_logins:
            return WriteStatus("blocked", "blocked — CROOKS_ALLOWED_LOGINS not configured")
        needed = {scope for op, scope in self._write_scopes().items() if operation is None or op == operation}
        if operation is not None and operation not in self._write_scopes():
            return WriteStatus("blocked", f"blocked — {operation.replace('_', ' ')} is not a change this Mac can make")
        try:
            granted = await self.shopify.access_scopes()
        except Exception as exc:  # noqa: BLE001
            # Shopify did not answer. That says nothing about what the app may do: refusing
            # here would tell the owner, out loud, that the store has not granted a scope it
            # may well have granted. The tap decides, and Shopify decides the tap.
            log.warning("could not read the Shopify app's scopes: %s", exc)
            return WriteStatus("unknown", f"ready, unverified — Shopify did not answer the scope check ({type(exc).__name__})")
        granted = set(granted)
        missing = sorted(needed - granted)
        if operation is not None:
            if missing:
                return WriteStatus("blocked", f"blocked — Shopify {', '.join(missing)} scope missing")
            return WriteStatus("ready", f"ready — {operation.replace('_', ' ')}")
        # The whole: blocked only when the store has granted none of it. A scope one change
        # needs and the store has not granted is named, and does not stop the others.
        scopes = self._write_scopes()
        ready_ops = sorted(op.replace("_", " ") for op, scope in scopes.items() if scope in granted)
        held_ops = sorted((op.replace("_", " "), scope) for op, scope in scopes.items() if scope not in granted)
        if not ready_ops:
            return WriteStatus("blocked", f"blocked — Shopify {', '.join(missing) or 'write'} scope missing")
        detail = f"ready — {', '.join(ready_ops)}"
        if held_ops:
            detail += "; " + ", ".join(f"{op} needs {scope}" for op, scope in held_ops)
        return WriteStatus("ready", detail)

    def _write_scopes(self) -> dict[str, str]:
        """operation → the Admin API scope its reviewed mutation needs, for every registered write."""
        from app.clients.shopify import REVIEWED_MUTATIONS
        from app.tools.registry import all_specs

        return {
            s.write.operation: REVIEWED_MUTATIONS[s.write.mutation].scope
            for s in all_specs()
            if s.write is not None and s.write.mutation in REVIEWED_MUTATIONS and not s.name.startswith("mock_")
        }

    def gmail_send_capability(self) -> dict[str, str]:
        """Whether an email could be sent from here. The inbox is authorised read-only until
        the owner runs the send authorisation deliberately (scripts/gmail_auth.py --send),
        and until then this says so rather than offering a send that would fail."""
        from app.clients.gmail import send_scope_granted

        if not self.settings.writes_enabled:
            return {"state": "disabled", "detail": "disabled — CROOKS_WRITES_ENABLED=false", "scope": "gmail.send"}
        if not self.settings.gmail_send_enabled:
            return {"state": "disabled", "detail": "disabled — CROOKS_GMAIL_SEND=false", "scope": "gmail.send"}
        try:
            granted = send_scope_granted()
        except Exception as exc:  # noqa: BLE001
            return {"state": "unknown", "detail": f"unverified — the Gmail credential could not be read ({type(exc).__name__})", "scope": "gmail.send"}
        if not granted:
            return {"state": "blocked", "detail": "Gmail send unavailable — scope missing (run: python scripts/gmail_auth.py --send)", "scope": "gmail.send"}
        return {"state": "ready", "detail": "ready — gmail send reply", "scope": "gmail.send"}

    async def capabilities(self) -> dict[str, dict[str, str]]:
        """Every change the Mac knows how to make, and whether it could make it now: the
        table /health shows and the order card's rail is built from. One scope read, cached,
        serves all of them; no mutation is ever sent to find out."""
        settings = self.settings
        scopes = self._write_scopes()
        out: dict[str, dict[str, str]] = {}
        if not settings.writes_enabled:
            state, detail, granted = "disabled", "disabled — CROOKS_WRITES_ENABLED=false", None
        elif not self.allowed_logins:
            state, detail, granted = "blocked", "blocked — CROOKS_ALLOWED_LOGINS not configured", None
        else:
            state, detail = "ready", ""
            try:
                granted = set(await self.shopify.access_scopes())
            except Exception as exc:  # noqa: BLE001
                state, detail, granted = "unknown", f"ready, unverified — Shopify did not answer the scope check ({type(exc).__name__})", None
        for operation, scope in sorted(scopes.items()):
            if state == "ready" and granted is not None and scope not in granted:
                out[operation] = {"state": "blocked", "detail": f"blocked — Shopify {scope} scope missing", "scope": scope}
            else:
                out[operation] = {"state": state, "detail": detail or f"ready — {operation.replace('_', ' ')}", "scope": scope}
        return out


@dataclass(frozen=True)
class WriteStatus:
    state: str     # "disabled" | "blocked" | "unknown" | "ready"
    detail: str

    @property
    def ready(self) -> bool:
        # "unknown" is the scope check having failed, not a refusal: a change may be applied
        # and Shopify has the final word on it.
        return self.state in ("ready", "unknown")

    @property
    def code(self) -> str:
        """The controlled refusal code a commit answers with while writes are not ready."""
        if self.state == "ready":
            return ""
        if "WRITES_ENABLED" in self.detail:
            return "writes_disabled"
        if "ALLOWED_LOGINS" in self.detail:
            return "allow_list_missing"
        return "scope_missing"


def build(settings: Settings | None = None) -> Runtime:
    settings = settings or get_settings()
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    settings.bench_audio_dir.mkdir(parents=True, exist_ok=True)

    sessions = get_manager(settings.session_idle_timeout_s)
    whisper = WhisperClient(settings.whisper_url, model=settings.whisper_model)
    scribe = ScribeClient(
        model=settings.scribe_model,
        language=settings.scribe_language,
        timeout_s=settings.scribe_timeout_s,
        base_url=settings.elevenlabs_base_url,
        max_keyterms=settings.scribe_max_keyterms,
        cooldown_s=settings.scribe_cooldown_s,
    )
    voice = VoiceClient(
        voice_id=settings.tts_voice_id,
        voice_name=settings.tts_voice_name,
        model=settings.tts_model,
        output_format=settings.tts_output_format,
        timeout_s=settings.tts_timeout_s,
        base_url=settings.elevenlabs_base_url,
        max_chars=settings.tts_max_chars,
        cooldown_s=settings.tts_cooldown_s,
        enabled=settings.tts_enabled,
    )
    voice.prefetch_enabled = settings.tts_prefetch
    normaliser = _build_normaliser(settings)
    transcriber = Transcriber(
        whisper,
        normaliser,
        scribe=scribe,
        primary=settings.stt_primary,
        keyterms=settings.scribe_keyterms,
        save_dir=settings.bench_audio_dir if settings.save_captures else None,
        max_saved=settings.max_saved_captures,
    )

    shopify = ShopifyClient(
        settings.shopify_shop_domain,
        settings.shopify_api_version,
        auth_mode=settings.shopify_auth_mode,
    )
    gmail = GmailClient()

    # Register the tool modules. Importing them is what runs the @tool decorators.
    from app.tools import gmail_tools, mock, shopify_tools, shopify_writes  # noqa: F401

    shopify_tools.bind(shopify)
    gmail_tools.bind(gmail, customer_lookup=_make_customer_lookup(shopify))

    kb = load(settings.kb_dir)
    provider = MaxAgentSDKProvider(
        system_prompt=build_system_prompt(kb, writes_enabled=settings.writes_enabled),
        model=settings.claude_model,
        session_lookup=sessions.get_or_create,
        tool_timeout_s=settings.tool_timeout_s,
        cli_path=settings.claude_cli_path,
        writes_enabled=settings.writes_enabled,
    )
    # The action engine is installed process-wide: the dispatcher stages into it from inside a
    # Claude turn, and the tablet's tap reaches it through the runtime. One index for both.
    actions = install_engine(ActionEngine(ledger=ActionLedger(settings.log_dir)))
    # A session the store lets go takes its proposals with it: nothing stays tappable, and
    # nothing of it stays in memory, once the conversation is over.
    if actions.forget_session not in sessions.on_drop:
        sessions.on_drop.append(actions.forget_session)

    if not settings.allowed_logins:
        log.warning(
            "CROOKS_ALLOWED_LOGINS is empty: any tailnet login may ask (reads only; changes need "
            "the allow-list). Open /whoami on the tablet and put its login in .env."
        )
    runtime = Runtime(
        build=web_build_id(),
        settings=settings,
        sessions=sessions,
        whisper=whisper,
        scribe=scribe,
        voice=voice,
        normaliser=normaliser,
        transcriber=transcriber,
        shopify=shopify,
        gmail=gmail,
        provider=provider,
        kb=kb,
        turnlog=TurnLog(settings.log_dir),
        actions=actions,
    )
    # The write policy (refund on cancel, restock, notify) is the runtime's settings, read
    # at prepare time, so a test's configured runtime is what the card prints.
    shopify_writes.bind_policy(lambda: runtime.settings)
    return runtime


def live_product_count(live: list[str]) -> int:
    """catalogue_terms() returns products then customers; a sentinel marks the boundary."""
    try:
        return live.index(CUSTOMER_BOUNDARY)
    except ValueError:
        return len(live)


CUSTOMER_BOUNDARY = "\x00customers"


def _build_normaliser(settings: Settings) -> Normaliser:
    seed = settings.kb_dir / "terminology.md"
    normaliser = from_file(seed)
    cache = settings.kb_dir / ".catalogue-cache.txt"
    if cache.exists():
        # A warm start uses last hour's live catalogue rather than falling back to the seed.
        try:
            cached = [t for t in cache.read_text(encoding="utf-8").splitlines() if t.strip()]
            normaliser.repoint(
                cached + list(normaliser.catalogue.terms), aliases=normaliser.catalogue.aliases
            )
        except OSError:
            pass
    return normaliser


def _make_customer_lookup(shopify: ShopifyClient):
    """Cross-reference an email sender against Shopify customers, cached per process.

    Gmail must keep working when Shopify does not, so a failure here returns None ("could not
    check"), never False ("not a customer") — those are different answers.
    """
    cache: dict[str, bool] = {}
    max_entries = 2000

    async def lookup(email: str) -> bool | None:
        email = (email or "").strip().lower()
        if not email:
            return None
        if email in cache:
            return cache[email]
        from app.tools.shopify_tools import _search_customers

        matches = await _search_customers(shopify, f"email:{email}", limit=1)
        if len(cache) >= max_entries:
            cache.clear()
        cache[email] = bool(matches)
        return cache[email]

    return lookup


def web_build_id(web_dir: Path | None = None) -> str:
    """A short fingerprint of the tablet page's files, so a page that has been open for days
    can tell that the Mac now serves a newer one."""
    import hashlib

    web_dir = web_dir or (Path(__file__).resolve().parent.parent / "web")
    digest = hashlib.sha1()
    try:
        for path in sorted(web_dir.glob("*")):
            if path.is_file():
                stat = path.stat()
                digest.update(f"{path.name}:{stat.st_size}:{int(stat.st_mtime)}\n".encode())
    except OSError:
        return "unknown"
    return digest.hexdigest()[:12]


def seed_paths(settings: Settings) -> list[Path]:
    return [settings.kb_dir, settings.bench_audio_dir, settings.log_dir]
