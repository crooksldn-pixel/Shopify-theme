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

import logging
import os
import shutil
import time

from app.providers.base import ClaudeProvider, ToolCall, TurnResult
from app.secrets import keychain
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

    # ------------------------------------------------------------ lifecycle

    async def start(self) -> None:
        assert_no_payg_credentials()
        keychain.get("claude_oauth_token")  # fail fast and loudly if it was never stored
        if not self._resolve_cli():
            raise RuntimeError(
                "The `claude` CLI is not on PATH. Under uvicorn the PATH differs from your "
                "shell — set CROOKS_CLAUDE_CLI_PATH to its absolute path."
            )
        self._started = True
        log.info("Claude provider ready (model=%s, subscription auth)", self._model)

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
            env={"CLAUDE_CODE_OAUTH_TOKEN": keychain.get("claude_oauth_token")},
        )

    @property
    def _hook(self):
        return make_pretooluse_hook(
            lambda: self._current, on_event=lambda name, _tier: self._states.append(name)
        )

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
        from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

        if not self._started:
            return TurnResult(
                text="The assistant is still starting up.",
                session_id=session_id,
                error_kind="not_started",
            )

        self._current = self._session_lookup(session_id) if self._session_lookup else None
        self._calls = []
        self._states = []
        started = time.perf_counter()

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
                    break
            answer = "\n".join(p.strip() for p in parts if p.strip()).strip()
        except Exception as exc:  # noqa: BLE001
            kind, spoken = classify_claude_error(exc)
            log.warning("turn failed (%s): %s", kind, exc)
            # A broken client cannot be reused; drop it so the next turn reconnects.
            await self.reset_session(session_id)
            return TurnResult(
                text=spoken, tool_calls=self._calls, session_id=session_id, error_kind=kind
            )
        finally:
            self._current = None

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
        try:
            keychain.get("claude_oauth_token")
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)
        return True, f"Agent SDK on Max subscription (model={self._model})"

    @property
    def last_tool_states(self) -> list[str]:
        """Tool names touched in the last turn, for the UI's CHECKING SHOPIFY / EMAIL states."""
        return list(self._states)


def classify_claude_error(exc: Exception) -> tuple[str, str]:
    """Map an SDK failure to a stable kind and the line the assistant should actually say."""
    text = f"{type(exc).__name__}: {exc}".lower()

    if "usage limit" in text or "rate_limit" in text or "429" in text:
        # Never retry this in a loop — retrying a usage-limit error spends more allowance.
        return "usage_limit", (
            "I have hit the Claude usage limit for now. It resets on a rolling five-hour "
            "window, so try again a little later."
        )
    if "oauth" in text or "401" in text or "unauthorized" in text or "authentication" in text:
        return "auth", (
            "My Claude login is not working. The subscription token may have expired — it "
            "needs renewing with claude setup-token."
        )
    if any(w in text for w in ("connection", "network", "dns", "unreachable", "timeout")):
        return "network", "I cannot reach Claude at the moment. It looks like a network problem."
    if "cli" in text or "enoent" in text or "no such file" in text:
        return "cli_missing", "The Claude command line tool is missing, so I cannot think."
    return "unknown", "Something went wrong while I was thinking. I have not got an answer."
