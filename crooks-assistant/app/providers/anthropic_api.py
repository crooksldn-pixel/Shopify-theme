"""Pay-as-you-go provider — deliberately unimplemented.

Day 1 runs entirely on the Claude Max subscription. This class exists to prove the provider
abstraction is real and to give a future migration somewhere to land. It imports no SDK and
looks up no key, so an accidental instantiation cannot start billing.
"""

from __future__ import annotations

from app.providers.base import ClaudeProvider, TurnResult


class AnthropicAPIProvider(ClaudeProvider):
    _WHY = (
        "AnthropicAPIProvider is a deliberate stub. Day 1 uses the Claude Max subscription via "
        "MaxAgentSDKProvider and must never consume pay-as-you-go credits. Implementing this "
        "class is a billing decision, not a coding one — raise it before writing a body."
    )

    async def start(self) -> None:
        raise NotImplementedError(self._WHY)

    async def stop(self) -> None:
        raise NotImplementedError(self._WHY)

    async def turn(self, session_id: str, text: str) -> TurnResult:
        raise NotImplementedError(self._WHY)

    async def health(self) -> tuple[bool, str]:
        raise NotImplementedError(self._WHY)

    async def reset_session(self, session_id: str) -> None:
        raise NotImplementedError(self._WHY)
