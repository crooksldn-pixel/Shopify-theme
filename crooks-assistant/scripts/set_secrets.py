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
}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print("usage: python scripts/set_secrets.py <key> [--delete]\n\nKeys:")
        for key in keychain.KNOWN_KEYS:
            mark = "stored" if keychain.present(key) else "not stored"
            print(f"  {key:<24} [{mark}]  {HELP.get(key, '')}")
        return 0

    key = sys.argv[1]
    if key not in keychain.KNOWN_KEYS:
        print(f"Unknown key {key!r}. Known: {', '.join(keychain.KNOWN_KEYS)}")
        return 1

    if "--delete" in sys.argv:
        keychain.delete(key)
        print(f"Deleted {key} from the {keychain.SERVICE} keychain entry.")
        return 0

    if keychain.present(key):
        if input(f"{key} is already stored. Replace it? [y/N] ").strip().lower() != "y":
            print("Unchanged.")
            return 0

    print(f"\n{key}\n{HELP.get(key, '')}\nThe value is hidden as you type or paste it.\n")
    value = getpass.getpass("value: ").strip()
    if not value:
        print("Nothing entered — unchanged.")
        return 1
    confirm = getpass.getpass("again:  ").strip()
    if value != confirm:
        print("The two entries do not match — unchanged.")
        return 1

    keychain.set_secret(key, value)
    # Length only. Printing any part of a secret to a terminal defeats the point of getpass.
    print(f"\nStored {key} ({len(value)} characters) in the macOS Keychain.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
