"""Returns, exchanges, replacements and resends (§21): the contract, not the change.

    app/returns/contract.py     the request shapes, what each change would be, and the refusal

Nothing here mutates anything, and nothing here is a second mutation path. When the scope is
granted the reviewed mutation becomes a `WriteSpec` through app/actions/engine.py like every
other change; the capability state the owner sees is in app/families/returns.py.
"""

from app.returns.contract import (
    CAPABILITIES,
    REASONS,
    InvalidRequest,
    NotAvailable,
    ReturnLine,
    ReturnRequest,
    ReviewedCapability,
    get,
    plan,
    stage,
    words,
)

__all__ = [
    "CAPABILITIES", "InvalidRequest", "NotAvailable", "REASONS", "ReturnLine", "ReturnRequest",
    "ReviewedCapability", "get", "plan", "stage", "words",
]
