"""Gmail read-only client.

The only scope requested is gmail.readonly, and the service is built with it hardcoded — there
is no configuration path that widens it. An expired credential is reported as "re-authorisation
required" with the command to run, never as a crash: an unattended backend that dies at 3am
because a token lapsed is worse than one that says so.
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("crooks.gmail")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_PATH = REPO_ROOT / "credentials.json"
TOKEN_PATH = REPO_ROOT / "token.json"


class GmailAuthRequired(RuntimeError):
    """The stored credential is missing or no longer valid. Needs a human, once."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            f"{detail} Re-authorise with: python scripts/gmail_auth.py"
        )


class GmailError(RuntimeError):
    """A Gmail call failed in a way worth reporting honestly."""


def load_credentials():
    """Load and refresh the stored credential. Never opens a browser."""
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    if not TOKEN_PATH.exists():
        raise GmailAuthRequired("No Gmail token stored.")

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds.valid:
        return creds

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError as exc:
            # invalid_grant is usually a Google password change (which revokes Gmail-scoped
            # tokens by design) or an app still in Testing (7-day token lifetime).
            raise GmailAuthRequired(f"Gmail refresh was rejected ({exc}).") from exc
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        TOKEN_PATH.chmod(0o600)
        return creds

    raise GmailAuthRequired("The stored Gmail credential cannot be refreshed.")


class GmailClient:
    def __init__(self) -> None:
        self._service = None

    def service(self):
        if self._service is None:
            from googleapiclient.discovery import build

            self._service = build(
                "gmail", "v1", credentials=load_credentials(), cache_discovery=False
            )
        return self._service

    def reset(self) -> None:
        self._service = None

    def profile(self) -> dict:
        return self.service().users().getProfile(userId="me").execute()

    def health(self) -> tuple[bool, str]:
        try:
            profile = self.profile()
            return True, f"{profile.get('emailAddress')} (read-only)"
        except GmailAuthRequired as exc:
            self.reset()
            return False, str(exc)
        except Exception as exc:  # noqa: BLE001
            return False, f"Gmail check failed: {exc}"
