"""Returns, exchanges, replacements and resends, as four states the owner can read (§21).

Each row says NOT_IMPLEMENTED and names the exact Shopify scope the change would need, because
that is the one thing the owner cannot work out from the tablet and the thing he would have to
go and grant. The contract behind them — the request shapes, the preconditions, the
verification, the refusal — is app/returns/contract.py; these rows are how it reaches /health,
the manifest, the settings sheet and the one prompt line that stops Claude attempting a return
and then apologising for it.

The states are declared here rather than derived, and that is correct rather than lazy: a
family's state is derived from the per-operation table when it HAS operations, and these have
none — there is no `WriteSpec` for a return, on purpose. The day there is, its operation goes
in `operations` and the row derives itself like every other write family; nothing else in this
file needs to change.
"""

from __future__ import annotations

from app.capabilities.families import CapabilityFamily, register
from app.returns import contract

# The reasons, in the order the contract states them, shortened to fit a row the owner reads.
_WHY = "the scope is not granted and the reviewed mutation is not written"

for capability in contract.CAPABILITIES.values():
    register(CapabilityFamily(
        key=capability.key,
        label=capability.label,
        area="orders",
        what=capability.what,
        # No operations: nothing is registered to stage, which is what NOT_IMPLEMENTED means.
        operations=(),
        tools=(),
        # The exact scope required, first and shortest — `families._said` shows one, and this
        # is the one to grant first. The rest are in `extra` for the settings sheet.
        scopes=capability.scopes,
        state="NOT_IMPLEMENTED",
        detail=_WHY,
        extra={
            "mutation": capability.mutation,
            "scopes_required": list(capability.scopes),
            "preconditions": list(capability.preconditions),
            "verification": capability.verification,
            "risk": capability.risk,
        },
    ))
