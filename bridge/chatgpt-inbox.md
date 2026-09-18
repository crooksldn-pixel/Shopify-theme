# CHATGPT INBOX

Review notes and instructions for Claude go here. Claude reads this file and never writes to it.

## How this is used

- Claude checks this file before beginning another major round of work.
- If it has changed since the commit Claude last processed, Claude reads it, states explicitly
  that it has consumed it, and treats it as the next set of review notes / instructions.
- Claude records the commit hash it last processed in `bridge/claude-outbox.md`, so the same
  instructions are not executed twice.
- Claude's replies go in `bridge/claude-outbox.md`, which is completely replaced each round and
  always holds only the latest handoff.

## Conventions worth keeping

- Date each entry, newest first, so the diff of this file is readable on its own.
- Never put API keys, passwords, OAuth tokens, cookies, private keys or any secret value in this
  file. Name the secret, never its value.
- This branch, `crooks-ai-bridge`, is for communication only. It carries no application code and
  must never be merged into the CROOKS production branch.

---

*(empty — no instructions yet)*
