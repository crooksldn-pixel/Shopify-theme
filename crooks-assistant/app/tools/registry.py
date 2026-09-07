"""Tool registry and the in-process MCP adapter.

Every capability the assistant has is a ToolSpec in this registry. The Agent SDK is given
`tools=[]` (no built-ins) and exactly one MCP server — the one built here — so the set of
things Claude can do in the running assistant is precisely the set of things registered below.
"""

from __future__ import annotations

import asyncio
import inspect
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from app.tools.gate import Tier

MCP_SERVER_NAME = "crooks"

Handler = Callable[..., Awaitable[Any]] | Callable[..., Any]


@dataclass(slots=True, frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    tier: Tier
    handler: Handler
    # Names of arguments carrying an id that must have been issued earlier this session.
    issued_id_args: tuple[str, ...] = field(default=())


class ToolError(RuntimeError):
    """A tool failed in a way the assistant should report honestly, not paper over."""


_REGISTRY: dict[str, ToolSpec] = {}


def tool(
    *,
    name: str,
    description: str,
    input_schema: dict[str, Any],
    tier: Tier = Tier.GREEN,
    issued_id_args: tuple[str, ...] = (),
) -> Callable[[Handler], Handler]:
    """Register a handler as a tool. The decorated function is returned unchanged so it stays
    directly callable from Python — which is how M5–M9 test tools without spending allowance."""

    def decorator(fn: Handler) -> Handler:
        if name in _REGISTRY:
            raise ValueError(f"Tool {name!r} is already registered.")
        _REGISTRY[name] = ToolSpec(
            name=name,
            description=description,
            input_schema=input_schema,
            tier=tier,
            handler=fn,
            issued_id_args=issued_id_args,
        )
        return fn

    return decorator


def get(name: str) -> ToolSpec:
    spec = _REGISTRY.get(normalise_tool_name(name))
    if spec is None:
        raise KeyError(f"No tool named {name!r}")
    return spec


def all_specs() -> list[ToolSpec]:
    return sorted(_REGISTRY.values(), key=lambda s: s.name)


def names() -> list[str]:
    return sorted(_REGISTRY)


def clear() -> None:
    """Test helper. Never called by the application."""
    _REGISTRY.clear()


def normalise_tool_name(name: str) -> str:
    """Strip the MCP prefix the SDK adds.

    Tool calls arrive as `mcp__crooks__shopify_find_order`, but the gate, the registry and the
    logs all speak in bare names. Classifying a prefixed name against a bare rule table is how
    a permission gate silently stops matching anything.
    """
    prefix = f"mcp__{MCP_SERVER_NAME}__"
    if name.startswith(prefix):
        return name[len(prefix) :]
    if name.startswith("mcp__"):
        # A differently-named server: take the last segment rather than guessing.
        return name.rsplit("__", 1)[-1]
    return name


async def invoke(name: str, args: dict[str, Any], *, timeout_s: float) -> Any:
    """Run a tool handler with a hard timeout. Does NOT consult the gate — callers must have
    cleared the call first. The single entry point for actually executing a handler."""
    spec = get(name)
    started = time.perf_counter()
    try:
        if inspect.iscoroutinefunction(spec.handler):
            result = await asyncio.wait_for(spec.handler(**args), timeout=timeout_s)
        else:
            result = await asyncio.wait_for(
                asyncio.to_thread(spec.handler, **args), timeout=timeout_s
            )
    except TimeoutError as exc:
        raise ToolError(
            f"{spec.name} did not respond within {timeout_s:.0f} seconds."
        ) from exc
    except TypeError as exc:
        raise ToolError(f"{spec.name} was called with arguments it does not accept: {exc}") from exc
    if isinstance(result, dict):
        result.setdefault("_ms", round((time.perf_counter() - started) * 1000, 1))
    return result


def build_mcp_server(dispatch: Callable[[str, dict[str, Any]], Awaitable[Any]]):
    """Expose the registry to the Agent SDK as an in-process MCP server.

    `dispatch` is the gated execution path from app/tools/dispatch.py — every tool the SDK can
    reach is wired to it, so there is no route from Claude to a handler that skips the gate.
    """
    from claude_agent_sdk import create_sdk_mcp_server
    from claude_agent_sdk import tool as sdk_tool

    sdk_tools = []
    for spec in all_specs():

        def make(spec: ToolSpec = spec):
            @sdk_tool(spec.name, spec.description, spec.input_schema)
            async def _run(args: dict[str, Any]) -> dict[str, Any]:
                payload = await dispatch(spec.name, args)
                return {"content": [{"type": "text", "text": payload}]}

            return _run

        sdk_tools.append(make())

    return create_sdk_mcp_server(name=MCP_SERVER_NAME, version="1.0.0", tools=sdk_tools)
