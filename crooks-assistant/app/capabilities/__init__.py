"""What CROOKS OS can actually do, generated from the registries rather than remembered.

app/capabilities/manifest.py builds the manifest from app/tools/registry.py,
app/analytics/query.py, app/presentation.py and the action grammar — so a tool added or
removed changes the answer to "what can you do?" without anyone editing a sentence.

app/capabilities/delta.py keeps the manifest of the previous build beside the current one,
so "what more can you do now?" is a comparison the Mac can make in milliseconds.

Three modules here are about the REQUEST rather than about the manifest, and they are here
because they decide when the manifest is the right answer at all (Phase 5 §4, §5, §23):

    ask.py         what a "can you …" sentence is actually asking. "can you" alone never
                   means a capability question; the operation, the entity or the task that
                   follows dominates it. Also the one list of the words that oblige a
                   surface, so the router and the report cannot disagree about them.
    ui_intent.py   the UI-intent contract: which words oblige a visible workspace, which
                   surfaces answer which demand, and the failure class a turn earns when the
                   words demanded a surface and none was drawn. Pure — no families, no reads.
    screen.py      what is actually on the glass, derived from the session against the fixed
                   chrome, so "nothing is on screen" has to be true before it is said.

They are imported on use rather than re-exported below: `ask` reads the router's vocabulary
and the router reads `ask`, and a module-level export here would close that circle.
"""

from app.capabilities.delta import delta, record_build, spoken_delta
from app.capabilities.manifest import build, fingerprint, spoken_summary

__all__ = ["build", "delta", "fingerprint", "record_build", "spoken_delta", "spoken_summary"]
