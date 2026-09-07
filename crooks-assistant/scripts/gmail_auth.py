#!/usr/bin/env python3
"""One-time Gmail authorisation, and a --verify mode that proves refresh works headlessly.

Before this will produce a durable token you must PUBLISH the Google Cloud consent screen.
An app left in Testing issues refresh tokens that expire after seven days, and an unattended
backend then stops working every week for no visible reason.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.clients.gmail import (  # noqa: E402
    CREDENTIALS_PATH,
    SCOPES,
    GmailAuthRequired,
    GmailClient,
    load_credentials,
    store_token_json,
)


def authorise() -> int:
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not CREDENTIALS_PATH.exists():
        print(
            f"{CREDENTIALS_PATH} not found.\n\n"
            "Google Cloud console → Clients → Create client → Desktop app → download the JSON\n"
            "and save it there. A Web client gives redirect_uri_mismatch."
        )
        return 1

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
    print("\nA browser will open. Expect an 'unverified app' warning — that is correct for a\n"
          "private app. Click Advanced, then 'Go to … (unsafe)', then Allow. Once, ever.\n")
    # 127.0.0.1 rather than localhost: Google warns localhost can trip client firewalls.
    # prompt=consent + access_type=offline: a re-authorisation without them can come back
    # with no refresh token at all, which is a credential that dies within the hour.
    creds = flow.run_local_server(
        host="127.0.0.1", port=0, open_browser=True, access_type="offline", prompt="consent"
    )
    if not creds.refresh_token:
        print("Google did not return a refresh token. Revoke the app at myaccount.google.com/permissions and run this again.")
        return 1

    where = store_token_json(creds.to_json())
    print(f"\nStored the Gmail credential in the {'macOS Keychain' if where == 'keychain' else 'token.json file (mode 600)'}.")
    return verify()


def verify() -> int:
    try:
        creds = load_credentials()
    except GmailAuthRequired as exc:
        print(f"FAIL: {exc}")
        return 1

    granted = list(creds.scopes or [])
    print(f"refresh token  : {'present' if creds.refresh_token else 'MISSING — re-run without --verify'}")
    print(f"scopes granted : {granted}")
    if granted != SCOPES:
        print(f"WARNING: expected exactly {SCOPES}. A wider scope than gmail.readonly is a bug.")

    client = GmailClient()
    profile = client.profile()
    print(f"account        : {profile.get('emailAddress')}")
    print(f"total messages : {profile.get('messagesTotal')}")

    service = client.service()
    listing = (
        service.users()
        .messages()
        .list(userId="me", q="newer_than:14d category:primary -in:chats", maxResults=5)
        .execute()
    )
    print("\nFive most recent Primary threads:")
    for stub in listing.get("messages", [])[:5]:
        message = (
            service.users()
            .messages()
            .get(userId="me", id=stub["id"], format="metadata", metadataHeaders=["Subject"])
            .execute()
        )
        subject = next(
            (h["value"] for h in message["payload"]["headers"] if h["name"] == "Subject"),
            "(no subject)",
        )
        print(f"  · {subject[:70]}")

    print(
        "\nNow restart this script with --verify in a fresh process. If it prints this same\n"
        "output without opening a browser, the refresh path works and M8 passes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(verify() if "--verify" in sys.argv else authorise())
