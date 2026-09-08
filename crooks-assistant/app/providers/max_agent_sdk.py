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
from app.tools.gate import Tier

log = logging.getLogger("crooks.claude")

# How long /cancel waits for the CLI to acknowledge an interrupt before giving up on it.
INTERRUPT_TIMEOUT_S = 5.0


# Every route by which the claude CLI could bill somewhere other than the subscription: a raw
# key, a bearer token, a key-helper script, or a cloud provider. Any of them set means stop.
PAYG_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_API_KEY_HELPER",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
)


class BillingGuardError(RuntimeError):
    """A pay-as-you-go credential is present. Refuse to run rather than spend money silently."""


def assert_no_payg_credentials() -> None:
    """Called at startup. The single most expensive mistake this project could make is to fall
    back to API billing without noticing, and the SDK will happily do that if a key is exported."""
    for name in PAYG_ENV_VARS:
        if os.environ.get(name):
            raise BillingGuardError(
                f"{name} is set in this environment. The assistant runs on the Claude Max "
                f"subscription and must never consume pay-as-you-go credit. Unset it (check "
                f"your shell profile) and start again. Do not remove this check."
            )


def withheld_tools(specs, *, writes_enabled: bool) -> set[str]:
    """The tools the model is never offered: a RED read, and every write while writes are off.
    Pure, so the rule can be checked without an SDK."""
    return {
        s.name for s in specs
        if (s.write is None and s.tier is Tier.RED) or (s.write is not None and not writes_enabled)
    }


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
        turn_timeout_s: float = 120.0,
        client_idle_timeout_s: float = 1800.0,
        writes_enabled: bool = False,
    ) -> None:
        self._system_prompt = system_prompt
        # Off: the write tools are not offered to the model at all, and are disallowed at the
        # SDK layer as well, so the assistant is the read-only one it always was.
        self._writes_enabled = writes_enabled
        self._model = model
        self._session_lookup = session_lookup
        self._tool_timeout_s = tool_timeout_s
        self._cli_path = cli_path
        self._max_turns = max_turns
        self._turn_timeout_s = turn_timeout_s
        self._client_idle_timeout_s = client_idle_timeout_s
        self._clients: dict[str, object] = {}
        self._client_last_used: dict[str, float] = {}
        # One client connected ahead of the next new conversation. Spawning the `claude`
        # subprocess and its MCP handshake is one to three seconds; paying it on the first
        # question of the day, or after "new conversation", is the pause that reads as slow.
        self._spare: object | None = None
        self._spare_task: asyncio.Task | None = None
        self._current: Session | None = None
        self._calls: list[ToolCall] = []
        self._states: list[str] = []
        # Where the time of the current turn went: ("model", ms) as each model step lands,
        # ("tool:<name>", ms) as each tool call returns. The measurement every later change needs.
        self._steps: list[tuple[str, float]] = []
        self._turn_started = 0.0
        self._sweep_task: asyncio.Task | None = None
        self._turn_epoch: int | None = None
        self._started = False
        self._auth_mode = "token"  # "token" (a stored setup-token) or "cli" (the CLI's own login)
        # One turn at a time. The tablet is single-user, and two overlapping turns would
        # share _current, _calls and the hook — a race that would misattribute tool calls.
        self._turn_lock = asyncio.Lock()

    # ------------------------------------------------------------ lifecycle

    async def start(self) -> None:
        assert_no_payg_credentials()
        # The SDK otherwise spawns `claude -v` before every connect and pre-warm: a Node
        # start-up (200-2000 ms) to learn a version this process pins itself.
        os.environ.setdefault("CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK", "1")
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
            # The CLI keeps its own login, in the login Keychain. That is the normal way this
            # runs: it works from a Terminal and from the login-time LaunchAgents `make
            # install` sets up, because both live in the user's session. It would not work
            # from a system daemon, which nothing here uses.
            if not cli_logged_in(cli):
                raise RuntimeError(
                    f"{exc} (and the claude CLI is not logged in either — run `claude`, then `/login`)."
                ) from exc
            self._auth_mode = "cli"
            log.info(
                "No claude_oauth_token in the Keychain; using the claude CLI's own login "
                "(auth=cli). This needs the Mac to be logged in, which `make up` and the "
                "`make install` launchd agents both are."
            )
        self._started = True
        log.info("Claude provider ready (model=%s, auth=%s)", self._model, self._auth_mode)
        self._prewarm_soon()

    async def stop(self) -> None:
        self._started = False   # first, so reset_session does not pre-warm a replacement
        for session_id in list(self._clients):
            await self.reset_session(session_id)
        await self._drop_spare()

    # ------------------------------------------------------------ pre-warming

    def _prewarm_soon(self) -> None:
        """Connect the next conversation's client in the background, if none is waiting."""
        if not self._started or self._spare is not None:
            return
        if self._spare_task is not None and not self._spare_task.done():
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        self._spare_task = loop.create_task(self._prewarm())

    async def _prewarm(self) -> None:
        from claude_agent_sdk import ClaudeSDKClient

        try:
            client = ClaudeSDKClient(options=self._options())
            await client.connect()
            await self._verify_auth_source(client)
        except BillingGuardError:
            # Cannot be raised from a background task to anyone; the next real connect will
            # raise it where it stops a turn. Say it loudly here as well.
            log.critical("pre-warmed claude client is billing an API key; dropped it")
            return
        except Exception as exc:  # noqa: BLE001
            log.warning("could not pre-warm a Claude client: %s", exc)
            return
        if self._started and self._spare is None:
            self._spare = client
        else:
            await _disconnect_quietly(client)

    async def _drop_spare(self) -> None:
        task, self._spare_task = self._spare_task, None
        if task is not None and not task.done():
            task.cancel()
        spare, self._spare = self._spare, None
        if spare is not None:
            await _disconnect_quietly(spare)

    def _resolve_cli(self) -> str:
        if self._cli_path:
            return self._cli_path if os.path.exists(self._cli_path) else ""
        return shutil.which("claude") or ""

    # -------------------------------------------------------------- options

    def _options(self):
        from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

        server = registry.build_mcp_server(self._dispatch)
        prefix = f"mcp__{registry.MCP_SERVER_NAME}__"
        # Refused twice: disallowed at the SDK layer, and denied by the hook if anything ever
        # reaches it. Belt and braces, because one barrier is one failure away. A RED read
        # never runs; a write is offered only when writes are on, and even then it is only
        # ever staged (app/tools/dispatch.py), never executed by the model's call.
        withheld = withheld_tools(registry.all_specs(), writes_enabled=self._writes_enabled)
        tool_names = [prefix + n for n in registry.names() if n not in withheld]
        disallowed = [prefix + n for n in sorted(withheld)]

        return ClaudeAgentOptions(
            system_prompt=self._system_prompt,
            model=self._model,
            # No built-in tools. Without this Claude can read and write this machine's files.
            tools=[],
            mcp_servers={registry.MCP_SERVER_NAME: server},
            allowed_tools=tool_names,
            disallowed_tools=disallowed,
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

    def _on_tool_event(self, name: str, tier: str, disposition: str = "EXECUTE_NOW") -> None:
        self._states.append(name)
        session = self._current
        denied = disposition == "DENY"
        if denied:
            # A hook-denied call never reaches dispatch, so record it here or the turn log
            # would show a refusal the model reported but no tool call behind it.
            reason = session.refusals[-1].reason if session and session.refusals else "refused"
            self._calls.append(ToolCall(name=name, args={}, ok=False, error=reason))
        if session is None:
            return
        if denied:
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
        if self._turn_epoch is not None and session.epoch != self._turn_epoch:
            log.info("tool call %s refused: the owner moved on (epoch %s → %s)", tool_name, self._turn_epoch, session.epoch)
            return "REFUSED: the owner has moved on to another question. Do not act on this one; answer briefly."
        try:
            return await dispatch(
                tool_name,
                args,
                session=session,
                timeout_s=self._tool_timeout_s,
                calls=self._calls,
            )
        finally:
            self._step(f"tool:{tool_name}")

    # ------------------------------------------------------------------ run

    async def _client_for(self, session_id: str):
        from claude_agent_sdk import ClaudeSDKClient

        await self._sweep_idle_clients()
        client = self._clients.get(session_id)
        if client is None:
            # Held open across turns. Recreating it per request costs seconds of subprocess
            # spin-up and throws away the conversation, which is what makes "and how much did
            # that come to?" work.
            if self._spare is not None:
                client, self._spare = self._spare, None   # connected and verified already
                log.info("new conversation took the pre-warmed client")
            else:
                client = ClaudeSDKClient(options=self._options())
                await client.connect()
                await self._verify_auth_source(client)
            self._clients[session_id] = client
            self._prewarm_soon()   # and the one after this gets the same head start
        self._client_last_used[session_id] = time.time()
        return client

    async def _sweep_idle_clients(self) -> None:
        """Each client is a `claude` subprocess. Sessions expire; their subprocesses must too."""
        now = time.time()
        for session_id, last in list(self._client_last_used.items()):
            if now - last > self._client_idle_timeout_s:
                await self.reset_session(session_id)

    async def _verify_auth_source(self, client) -> None:
        """Ask the running CLI how it authenticated. Belt and braces over the env check: if it
        reports an API key, stop before a single token is billed."""
        try:
            info = await client.get_server_info()
        except Exception:  # noqa: BLE001 — informational; absence is not a failure
            return
        if not isinstance(info, dict):
            return
        # The CLI nests these under `account` (measured: top-level lookups logged '?').
        account = info.get("account") if isinstance(info.get("account"), dict) else {}
        source = str(
            account.get("apiKeySource") or info.get("apiKeySource") or info.get("api_key_source") or ""
        ).lower()
        provider = str(
            account.get("apiProvider") or info.get("apiProvider") or info.get("api_provider") or ""
        ).lower()
        log.info("claude auth source=%r provider=%r", source or "?", provider or "?")
        if source and any(k in source for k in ("api_key", "apikey", "ANTHROPIC_API_KEY".lower())):
            raise BillingGuardError(
                f"The claude CLI reports it is authenticating with an API key ({source}). "
                "That is pay-as-you-go billing. Refusing to continue."
            )

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
        self._steps = []
        started = time.perf_counter()
        self._turn_started = started
        # The conversation position this turn answers. A /cancel or a later question moves the
        # session past it; a tool call arriving after that acts for nobody and is refused.
        self._turn_epoch = session.epoch if session is not None else None
        if session is not None:
            session.set_state("THINKING")
            session.turns += 1

        result_message = None
        try:
            client = await self._client_for(session_id)

            async def run() -> tuple[str, object]:
                await client.query(text)
                parts: list[str] = []
                last = None
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        self._step("model")
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                parts.append(block.text)
                    elif isinstance(message, ResultMessage):
                        last = message
                        break
                return "\n".join(p.strip() for p in parts if p.strip()).strip(), last

            # A stalled CLI must not hold the turn lock forever.
            answer, result_message = await asyncio.wait_for(run(), timeout=self._turn_timeout_s)
        except TimeoutError:
            log.warning("turn timed out after %.0fs; dropping the client", self._turn_timeout_s)
            await self.reset_session(session_id)
            if session is not None:
                session.set_state("ERROR", "timeout")
            return TurnResult(
                text="That took too long and I have given up on it. Ask me again.",
                tool_calls=self._calls, session_id=session_id, error_kind="timeout",
            )
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
        # The conversation was used to the end of this turn: its subprocess and its session
        # expire from the same moment, so "that order" cannot be forgotten silently.
        self._client_last_used[session_id] = time.time()
        log.info(
            "turn ok in %.0f ms, %d tool call(s): %s",
            (time.perf_counter() - started) * 1000,
            len(self._calls),
            " ".join(f"{name}@{ms:.0f}" for name, ms in self._steps) or "-",
        )
        return TurnResult(text=answer, tool_calls=self._calls, session_id=session_id, steps=list(self._steps))

    def _step(self, name: str) -> None:
        if self._turn_started:
            self._steps.append((name, round((time.perf_counter() - self._turn_started) * 1000, 1)))

    async def set_system_prompt(self, prompt: str) -> None:
        """A new knowledge base means a new system prompt, and the SDK fixes the prompt when a
        client connects — so every open client is dropped. The next turn reconnects with the
        new prompt; the conversation history is lost, which is the honest trade."""
        self._system_prompt = prompt
        for session_id in list(self._clients):
            await self.reset_session(session_id)
        await self._drop_spare()   # it was connected with the old prompt
        self._prewarm_soon()

    async def interrupt(self, session_id: str) -> bool:
        """Ask the CLI to stop the turn it is running for this session. The turn then ends
        with whatever text it had, and the lock is released for the question that replaced
        it. True when there was a client to interrupt."""
        client = self._clients.get(session_id)
        if client is None or self._current is None or self._current.session_id != session_id:
            return False
        try:
            # The SDK's control request would wait a minute on a wedged CLI; the owner's next
            # question is already being asked, and the turn lock is what it waits for.
            await asyncio.wait_for(client.interrupt(), timeout=INTERRUPT_TIMEOUT_S)
        except TimeoutError:
            log.warning("interrupt for %s got no answer in %.0fs", session_id, INTERRUPT_TIMEOUT_S)
            return False
        except Exception as exc:  # noqa: BLE001 — a turn that already ended is not a failure
            log.info("interrupt for %s did nothing: %s", session_id, exc)
            return False
        return True

    async def reset_session(self, session_id: str) -> None:
        client = self._clients.pop(session_id, None)
        self._client_last_used.pop(session_id, None)
        if client is not None:
            await _disconnect_quietly(client)
        self._prewarm_soon()   # "new conversation" is about to want one

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
        note = (
            "" if self._auth_mode == "token"
            else " — the CLI's own login; needs a logged-in Mac (make up / make install launchd agents)"
        )
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
        "My Claude login is not working on the Mac. Run claude there and sign in again with "
        "slash login."
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
        when = local_clock(when)
        return f"I have hit the Claude usage limit. It resets {joiner} {when}. I will not retry on my own."
    return RESULT_SPOKEN["usage_limit"]


_UTC_CLOCK = re.compile(r"^(\d{1,2}):(\d{2})\s*(?:UTC|GMT|Z)$", re.I)


def local_clock(when: str) -> str:
    """"15:00 UTC" as the Mac's own clock: "four o'clock" in London in summer. Anything that
    is not a bare UTC time is read out as it came."""
    match = _UTC_CLOCK.match(when.strip())
    if not match:
        return when
    from datetime import UTC, datetime

    hour, minute = int(match.group(1)), int(match.group(2))
    now = datetime.now(UTC)
    local = now.replace(hour=hour % 24, minute=minute, second=0, microsecond=0).astimezone()
    return local.strftime("%H:%M")


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


async def _disconnect_quietly(client) -> None:
    try:
        await client.disconnect()
    except Exception:  # noqa: BLE001 — the subprocess may already be gone
        pass


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
