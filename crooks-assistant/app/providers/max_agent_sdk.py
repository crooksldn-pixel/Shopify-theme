"""Claude via the Agent SDK on the Max subscription.

Three properties this module exists to guarantee:

1. No pay-as-you-go credential is ever used. The process refuses to boot if ANTHROPIC_API_KEY
   is set, and the OAuth token is injected into the SDK subprocess environment only.
2. Claude has no capability except our tools. `tools=[]` removes every built-in (no filesystem,
   no bash, no web), `setting_sources=[]` stops it inheriting settings, skills or plugins from
   this machine, and exactly one in-process MCP server is registered.
3. The gate sees every call. `permission_mode="dontAsk"` means nothing prompts a human who is
   not there — so a PreToolUse hook, which fires even for auto-approved tools, does the gating.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import time

from app.providers.base import ClaudeProvider, ToolCall, TurnResult
from app.secrets import keychain
from app.secrets.keychain import SecretMissing
from app.session.models import Session
from app.tools import registry
from app.tools.dispatch import dispatch, make_pretooluse_hook

log = logging.getLogger("crooks.claude")


class BillingGuardError(RuntimeError):
    """A pay-as-you-go credential is present. Refuse to run rather than spend money silently."""


def assert_no_payg_credentials() -> None:
    """Called at startup. The single most expensive mistake this project could make is to fall
    back to API billing without noticing, and the SDK will happily do that if a key is exported."""
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        if os.environ.get(name):
            raise BillingGuardError(
                f"{name} is set in this environment. The assistant runs on the Claude Max "
                f"subscription and must never consume pay-as-you-go credit. Unset it (check "
                f"your shell profile) and start again. Do not remove this check."
            )


class MaxAgentSDKProvider(ClaudeProvider):
    def __init__(
        self,
        *,
        system_prompt: str,
        model: str = "sonnet",
        session_lookup=None,
        tool_timeout_s: float = 8.0,
        cli_path: str = "",
        max_turns: int = 12,
    ) -> None:
        self._system_prompt = system_prompt
        self._model = model
        self._session_lookup = session_lookup
        self._tool_timeout_s = tool_timeout_s
        self._cli_path = cli_path
        self._max_turns = max_turns
        self._clients: dict[str, object] = {}
        self._current: Session | None = None
        self._calls: list[ToolCall] = []
        self._states: list[str] = []
        self._started = False
        self._auth_mode = "token"  # "token" (Keychain, works under launchd) or "cli" (login session only)
        # One turn at a time. The tablet is single-user, and two overlapping turns would
        # share _current, _calls and the hook — a race that would misattribute tool calls.
        self._turn_lock = asyncio.Lock()

    # ------------------------------------------------------------ lifecycle

    async def start(self) -> None:
        assert_no_payg_credentials()
        cli = self._resolve_cli()
        if not cli:
            raise RuntimeError(
                "The `claude` CLI is not on PATH. Under uvicorn the PATH differs from your "
                "shell — set CROOKS_CLAUDE_CLI_PATH to its absolute path."
            )
        try:
            keychain.get("claude_oauth_token")
            self._auth_mode = "token"
        except SecretMissing as exc:
            # The CLI keeps its own login. That works while a user session is logged in — fine
            # for `make dev` — but launchd runs outside it and will fail. Say so, loudly, once.
            if not cli_logged_in(cli):
                raise RuntimeError(
                    f"{exc} (and the claude CLI is not logged in either — run `claude /login`)."
                ) from exc
            self._auth_mode = "cli"
            log.warning(
                "No claude_oauth_token in the Keychain; using the claude CLI's own login. This "
                "works interactively but NOT under launchd. Before M13: `claude setup-token` "
                "then `python scripts/set_secrets.py claude_oauth_token`."
            )
        self._started = True
        log.info("Claude provider ready (model=%s, auth=%s)", self._model, self._auth_mode)

    async def stop(self) -> None:
        for session_id in list(self._clients):
            await self.reset_session(session_id)
        self._started = False

    def _resolve_cli(self) -> str:
        if self._cli_path:
            return self._cli_path if os.path.exists(self._cli_path) else ""
        return shutil.which("claude") or ""

    # -------------------------------------------------------------- options

    def _options(self):
        from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

        server = registry.build_mcp_server(self._dispatch)
        tool_names = [f"mcp__{registry.MCP_SERVER_NAME}__{n}" for n in registry.names()]

        return ClaudeAgentOptions(
            system_prompt=self._system_prompt,
            model=self._model,
            # No built-in tools. Without this Claude can read and write this machine's files.
            tools=[],
            mcp_servers={registry.MCP_SERVER_NAME: server},
            allowed_tools=tool_names,
            # Nobody is sitting at a terminal to answer a prompt, so nothing may prompt. The
            # gate, not an interactive approval, is what makes this safe.
            permission_mode="dontAsk",
            # Auto-approved tools never reach can_use_tool. The hook fires regardless, which is
            # why the gate lives here and not there.
            hooks={"PreToolUse": [HookMatcher(hooks=[self._hook])]},
            # Do not inherit CLAUDE.md, settings, skills or plugins from this machine.
            setting_sources=[],
            max_turns=self._max_turns,
            cli_path=self._resolve_cli() or None,
            env=(
                {"CLAUDE_CODE_OAUTH_TOKEN": keychain.get("claude_oauth_token")}
                if self._auth_mode == "token"
                else {}
            ),
        )

    @property
    def _hook(self):
        return make_pretooluse_hook(lambda: self._current, on_event=self._on_tool_event)

    def _on_tool_event(self, name: str, tier: str) -> None:
        self._states.append(name)
        session = self._current
        if session is None:
            return
        if tier == "RED":
            session.set_state("THINKING", f"refused {name}")
        elif name.startswith("shopify_"):
            session.set_state("CHECKING SHOPIFY", name)
        elif name.startswith("gmail_"):
            session.set_state("CHECKING EMAIL", name)
        else:
            session.set_state("THINKING", name)

    async def _dispatch(self, tool_name: str, args: dict) -> str:
        session = self._current
        if session is None:
            return "ERROR: no active session for this tool call."
        return await dispatch(
            tool_name,
            args,
            session=session,
            timeout_s=self._tool_timeout_s,
            calls=self._calls,
        )

    # ------------------------------------------------------------------ run

    async def _client_for(self, session_id: str):
        from claude_agent_sdk import ClaudeSDKClient

        client = self._clients.get(session_id)
        if client is None:
            # Held open across turns. Recreating it per request costs seconds of subprocess
            # spin-up and throws away the conversation, which is what makes "and how much did
            # that come to?" work.
            client = ClaudeSDKClient(options=self._options())
            await client.connect()
            self._clients[session_id] = client
        return client

    async def turn(self, session_id: str, text: str) -> TurnResult:

        if not self._started:
            return TurnResult(
                text="The assistant is still starting up.",
                session_id=session_id,
                error_kind="not_started",
            )

        async with self._turn_lock:
            return await self._turn_locked(session_id, text)

    async def _turn_locked(self, session_id: str, text: str) -> TurnResult:
        from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

        session = self._session_lookup(session_id) if self._session_lookup else None
        self._current = session
        self._calls = []
        self._states = []
        started = time.perf_counter()
        if session is not None:
            session.set_state("THINKING")
            session.turns += 1

        result_message = None
        try:
            client = await self._client_for(session_id)
            await client.query(text)
            parts: list[str] = []
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            parts.append(block.text)
                elif isinstance(message, ResultMessage):
                    result_message = message
                    break
            answer = "\n".join(p.strip() for p in parts if p.strip()).strip()
        except Exception as exc:  # noqa: BLE001
            kind, spoken = classify_claude_error(exc)
            log.warning("turn failed (%s): %s", kind, exc)
            # A broken client cannot be reused; drop it so the next turn reconnects.
            await self.reset_session(session_id)
            if session is not None:
                session.set_state("ERROR", kind)
            return TurnResult(
                text=spoken, tool_calls=self._calls, session_id=session_id, error_kind=kind
            )
        finally:
            self._current = None

        # The SDK reports many failures as a ResultMessage rather than an exception — a usage
        # limit, max_turns, an API error. Read it, or a silent failure becomes a blank answer.
        kind = result_kind(result_message)
        if kind is not None:
            spoken = RESULT_SPOKEN.get(kind, RESULT_SPOKEN["unknown"])
            if kind == "usage_limit":
                spoken = usage_limit_line(_result_text(result_message))
            log.warning("turn ended with %s: %s", kind, _result_text(result_message)[:300])
            if kind in {"usage_limit", "auth", "api_error"}:
                await self.reset_session(session_id)
            if session is not None:
                session.set_state("ERROR", kind)
            return TurnResult(
                text=answer or spoken, tool_calls=self._calls, session_id=session_id,
                error_kind=kind, stopped_early=kind == "max_turns",
            )

        if result_message is not None and getattr(result_message, "permission_denials", None):
            log.info("SDK recorded %d permission denial(s) this turn", len(result_message.permission_denials))

        if session is not None:
            session.set_state("READY")
        log.info(
            "turn ok in %.0f ms, %d tool call(s)",
            (time.perf_counter() - started) * 1000,
            len(self._calls),
        )
        return TurnResult(text=answer, tool_calls=self._calls, session_id=session_id)

    async def reset_session(self, session_id: str) -> None:
        client = self._clients.pop(session_id, None)
        if client is not None:
            try:
                await client.disconnect()
            except Exception:  # noqa: BLE001
                pass

    async def health(self) -> tuple[bool, str]:
        if not self._started:
            return False, "Claude provider not started."
        if not self._resolve_cli():
            return False, "claude CLI not found on PATH."
        if self._auth_mode == "token":
            try:
                keychain.get("claude_oauth_token")
            except Exception as exc:  # noqa: BLE001
                return False, str(exc)
        note = "" if self._auth_mode == "token" else " — CLI login only; will NOT survive launchd"
        return True, f"Agent SDK on Max subscription (model={self._model}, auth={self._auth_mode}{note})"

    @property
    def last_tool_states(self) -> list[str]:
        """Tool names touched in the last turn, for the UI's CHECKING SHOPIFY / EMAIL states."""
        return list(self._states)


RESULT_SPOKEN = {
    "usage_limit": (
        "I have hit the Claude usage limit for now. It resets on a rolling five-hour window, "
        "so try again a little later."
    ),
    "max_turns": "That took more steps than I allow myself. Here is as far as I got.",
    "auth": (
        "My Claude login is not working. The subscription token may have expired — it needs "
        "renewing with claude setup-token."
    ),
    "api_error": "Claude returned an error, so I have not got an answer.",
    "unknown": "Something went wrong while I was thinking. I have not got an answer.",
}

_RESET_AT = re.compile(
    r"(?:reset|resets|try again|available)\s*(?:at|in|on)?\s*"
    r"([0-9]+\s*(?:minutes?|mins?|hours?|hrs?)"          # "in 45 minutes"
    r"|[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]+Z?"              # ISO timestamp
    r"|[0-9]{1,2}(?::[0-9]{2})?\s*(?:am|pm)\b(?:\s*\(?[A-Z]{2,4}\)?)?"  # "3pm (UTC)"
    r"|[0-9]{1,2}:[0-9]{2}(?:\s*\(?[A-Z]{2,4}\)?)?)",     # "15:00 UTC"
    re.I,
)


def usage_limit_line(detail: str) -> str:
    """Read the reset time back if the error carries one. No retry loop, ever."""
    match = _RESET_AT.search(detail or "")
    if match:
        when = match.group(1).strip()
        when = when.rstrip(")").replace("(", "")
        joiner = "in" if re.match(r"^\d+\s*(minutes?|mins?|hours?|hrs?)$", when, re.I) else "at"
        return f"I have hit the Claude usage limit. It resets {joiner} {when}. I will not retry on my own."
    return RESULT_SPOKEN["usage_limit"]


def _result_text(message) -> str:
    if message is None:
        return ""
    parts = [str(getattr(message, "result", "") or "")]
    errors = getattr(message, "errors", None) or []
    parts.extend(str(e) for e in errors)
    return " ".join(p for p in parts if p)


def result_kind(message) -> str | None:
    """Classify a ResultMessage. None means the turn genuinely succeeded."""
    if message is None:
        return None
    subtype = str(getattr(message, "subtype", "") or "")
    is_error = bool(getattr(message, "is_error", False))
    status = getattr(message, "api_error_status", None)
    text = (subtype + " " + _result_text(message)).lower()
    if not is_error and subtype in {"", "success"}:
        return None
    if "max_turns" in subtype:
        return "max_turns"
    if status == 429 or "usage limit" in text or "rate limit" in text or "rate_limit" in text:
        return "usage_limit"
    if status in (401, 403) or "oauth" in text or "unauthorized" in text or "authentication" in text:
        return "auth"
    if status is not None and status >= 400:
        return "api_error"
    return "unknown" if is_error else None


def cli_logged_in(cli_path: str) -> bool:
    """Ask the CLI itself whether it holds a login. Never reads or prints the credential."""
    try:
        out = subprocess.run(
            [cli_path, "auth", "status"], capture_output=True, text=True, timeout=20
        )
        payload = json.loads(out.stdout or "{}")
        return bool(payload.get("loggedIn"))
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


def classify_claude_error(exc: Exception) -> tuple[str, str]:
    """Map an SDK failure to a stable kind and the line the assistant should actually say."""
    try:
        from claude_agent_sdk import CLIConnectionError, CLINotFoundError, ProcessError
    except ImportError:  # pragma: no cover
        CLIConnectionError = CLINotFoundError = ProcessError = ()  # type: ignore[assignment]

    text = f"{type(exc).__name__}: {exc}".lower()

    if isinstance(exc, CLINotFoundError):
        return "cli_missing", "The Claude command line tool is missing, so I cannot think."
    if isinstance(exc, ProcessError):
        stderr = str(getattr(exc, "stderr", "") or "").lower()
        text = f"{text} {stderr}"
    if "usage limit" in text or "rate_limit" in text or "rate limit" in text or "429" in text:
        # Never retry this in a loop — retrying a usage-limit error spends more allowance.
        return "usage_limit", usage_limit_line(text)
    if "oauth" in text or "401" in text or "unauthorized" in text or "authentication" in text:
        return "auth", (
            "My Claude login is not working. The subscription token may have expired — it "
            "needs renewing with claude setup-token."
        )
    if isinstance(exc, CLIConnectionError) or any(
        w in text for w in ("connection", "network", "dns", "unreachable", "timeout")
    ):
        return "network", "I cannot reach Claude at the moment. It looks like a network problem."
    if "cli" in text or "enoent" in text or "no such file" in text:
        return "cli_missing", "The Claude command line tool is missing, so I cannot think."
    return "unknown", "Something went wrong while I was thinking. I have not got an answer."
