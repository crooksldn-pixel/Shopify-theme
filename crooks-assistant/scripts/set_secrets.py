#!/usr/bin/env python3
"""Store a secret in the macOS Keychain.

The value is typed at this prompt, never echoed, never written to a file, never passed as an
argument (which would put it in your shell history and in `ps`), and never printed back.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.secrets import keychain  # noqa: E402

HELP = {
    "claude_oauth_token": "Run `claude setup-token` and paste the one-year token.",
    "shopify_client_id": "Dev Dashboard app → Client ID (older docs call this the API key).",
    "shopify_client_secret": "Dev Dashboard app → Client secret.",
    "shopify_static_token": "Legacy shpat_… Admin API token. Fallback only — see M6.",
    "gmail_token": "Written by `make gmail`; you never type this one.",
    "elevenlabs_api_key": "ElevenLabs → Profile → API key. Scribe v2 hears you; Derek answers.",
}


# The keys `make secrets` walks through, in the order the milestones need them. The two
# fallbacks are skipped unless asked for by name.
WALKTHROUGH = (
    "claude_oauth_token",
    "shopify_client_id",
    "shopify_client_secret",
    "elevenlabs_api_key",
)


def store_one(key: str) -> int:
    if keychain.present(key):
        print(f"\n{key} is already stored.")
        if input("Replace it? [y/N] ").strip().lower() != "y":
            print("Kept.")
            return 0
    print(f"\n{key}\n{HELP.get(key, '')}\nThe value is hidden as you type or paste it.\n")
    value = getpass.getpass("value: ").strip()
    if not value:
        print("Nothing entered — skipped.")
        return 1
    confirm = getpass.getpass("again:  ").strip()
    if value != confirm:
        print("The two entries do not match — skipped.")
        return 1
    keychain.set_secret(key, value)
    # Length only. Printing any part of a secret to a terminal defeats the point of getpass.
    print(f"Stored {key} ({len(value)} characters) in the macOS Keychain.")
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print("usage: python scripts/set_secrets.py --all | <key> [--delete]\n\nKeys:")
        for key in keychain.KNOWN_KEYS:
            mark = "stored" if keychain.present(key) else "not stored"
            print(f"  {key:<24} [{mark}]  {HELP.get(key, '')}")
        return 0

    if sys.argv[1] == "--all":
        print("Storing the secrets the assistant needs. Press Enter with nothing typed to skip one.")
        failures = 0
        for key in WALKTHROUGH:
            failures += store_one(key)
        print("\nDone." if not failures else f"\nDone, {failures} skipped — run `make secrets` again for those.")
        return 0

    key = sys.argv[1]
    if key not in keychain.KNOWN_KEYS:
        print(f"Unknown key {key!r}. Known: {', '.join(keychain.KNOWN_KEYS)}")
        return 1

    if "--delete" in sys.argv:
        keychain.delete(key)
        print(f"Deleted {key} from the {keychain.SERVICE} keychain entry.")
        return 0

    return store_one(key)


if __name__ == "__main__":
    raise SystemExit(main())
