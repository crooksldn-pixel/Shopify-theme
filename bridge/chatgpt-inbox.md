# CHATGPT INBOX

## 2026-09-19 — Owner approval: bounded package fetching + BE-04 completion

Owner decision: **APPROVED — bounded package fetching for Builder Environment reconstruction.**

This is a continuation of ENV-REPRO-001 only. Do not rebuild or re-run already accepted evidence unnecessarily. Work from the published Builder repair candidate `claude/builder-environment-repair-review` @ `326c150b778afdc2b5881b2f7ac97e140e476eab` and preserve exact candidate/evidence identity. Do not merge or deploy.

### Approved network boundary

The Builder Environment may make read-only network downloads solely to reconstruct the declared, pinned development environment from a fresh/disposable checkout.

Requirements:
- only dependencies/tools explicitly declared by the committed Builder manifest/lockfiles;
- fetch only from the normal authoritative upstream/package sources for those declared dependencies/tools;
- pin release tags, asset URLs and versions rather than deriving ambiguous release URLs at runtime;
- preserve and enforce integrity verification; fail closed on version, checksum, provenance, verification or fetch failure;
- record install-time provenance needed to make the SkillSpector pin verifiable;
- no secrets or credentials;
- no production changes;
- no deployment;
- no CROOKS application writes;
- no privilege expansion;
- no unrelated/arbitrary network access;
- no destructive actions;
- use an isolated/disposable Builder reconstruction environment, not production.

### Objective

Finish the remaining BE-04 acceptance work identified in the previous outbox:
1. pin the required release tags and exact asset URLs in repository-controlled inputs;
2. make the reconstruction plan fully executable with integrity checks;
3. execute the complete reconstruction from a genuinely fresh/disposable checkout using only repository-controlled inputs plus the approved read-only fetches;
4. run the reconstruction a second time and prove the intended idempotent/repeatable behaviour;
5. close the SkillSpector provenance gap if it can be done within this bounded scope;
6. add/adjust regression tests for the completed behaviour.

Because the candidate changes, prior candidate-bound review evidence is invalid for the changed tree. Re-run the relevant independent gates against the exact final candidate and bind evidence to its final SHA. Verify BE-01 through BE-04 against that exact final candidate rather than trusting prior prose.

Also update the existing contract-trial record with what this continuation actually exercises. Do not claim publication-retry, obsolete-result fencing, or integration re-verification as exercised unless they genuinely occur. Preserve the previously identified CG-01 through CG-05 gaps rather than silently working around them.

Publish the exact final candidate to `claude/builder-environment-repair-review`, read the remote identity back, replace `bridge/claude-outbox.md` with the SHA-bound evidence and STOP for independent Director review.

### Still prohibited

No production promotion/deployment, no service/Tailscale changes, no secrets, no enabling CROOKS writes, no permission widening, no destructive migration/action, no new external spend, and no Engineering Orchestrator implementation in this round.
