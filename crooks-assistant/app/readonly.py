"""A latch that makes this process incapable of changing anything, anywhere.

It exists for one job: letting the experience suite run against the real store and the real
inbox — real orders, real threads, real correlations, so that what is being looked at is what
the owner would actually see — without any possibility that the run sends an email, cancels an
order or archives a thread.

The rule it keeps is not "the tests are careful". It is that once the latch is down, the two
functions that can change anything refuse before they do it:

    app/clients/shopify.py  ShopifyClient.mutate    — every reviewed Shopify mutation
    app/clients/gmail.py    GmailClient send/draft/modify — every Gmail change

Every write in the application funnels through those, so this is a complete set rather than a
list of the ones that were remembered. The action engine checks it too, one layer up, so that a
refusal reads as a policy decision on the card rather than as a client error in a log.

Three properties make it a safety device rather than a setting:

- **Off unless a person put it on.** Nothing engages it but an explicit call, and the only
  caller is the experience runner's entry point. No request, header, form field or environment
  variable reaches it, so it cannot be turned ON by accident — or, more importantly, OFF.
- **One way.** There is no release. A process that has been read-only stays read-only for its
  life; the way to write again is to start a process that never latched. A releasable latch is
  one a later line of code can release.
- **Loud.** Engaging is logged, and every refusal is logged with what was refused.

It restricts; it never permits. Nothing here can make a write possible that was not already —
the allow-list, the gesture, the scopes, the staging and the verification all still apply, and
this is simply a floor underneath them.
"""

from __future__ import annotations

import logging

log = logging.getLogger("crooks.readonly")

_engaged = False
_reason = ""


class WriteRefused(RuntimeError):
    """A change was attempted in a process that cannot make one."""


def engage(reason: str) -> None:
    """Latch this process read-only, for the stated reason. There is no way back."""
    global _engaged, _reason
    if _engaged:
        return
    _engaged = True
    _reason = str(reason or "read-only mode")[:200]
    log.warning("READ-ONLY MODE ENGAGED: %s. No Shopify or Gmail change can be executed by this process.", _reason)


def active() -> bool:
    return _engaged


def reason() -> str:
    return _reason


def assert_writable(what: str) -> None:
    """Raise unless this process may change things. Called at the two client chokepoints and
    again in the action engine, because one check is a check and two are a floor."""
    if _engaged:
        log.warning("READ-ONLY MODE refused a change: %s", what)
        raise WriteRefused(
            f"Refused: this process is in read-only mode ({_reason}), so {what} cannot be executed."
        )


def banner() -> str:
    """One line for a report or a log header, so a run can never be mistaken for a live one."""
    return f"LIVE READ-ONLY TEST MODE — {_reason}" if _engaged else ""
