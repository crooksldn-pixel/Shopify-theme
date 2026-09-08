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


def _read_token_json() -> tuple[str, str]:
    """(json, where). The Keychain is preferred — the refresh token is a long-lived secret and
    the project rule is that secrets do not live in files. token.json (mode 600) remains the
    fallback for the plan's original flow and for hosts without a keychain."""
    from app.secrets import keychain

    stored = keychain.get_optional("gmail_token")
    if stored:
        return stored, "keychain"
    if TOKEN_PATH.exists():
        return TOKEN_PATH.read_text(encoding="utf-8"), "file"
    raise GmailAuthRequired("No Gmail token stored.")


def store_token_json(payload: str) -> str:
    """Persist the authorised-user JSON. Returns where it went."""
    from app.secrets import keychain

    try:
        keychain.set_secret("gmail_token", payload)
        if TOKEN_PATH.exists():
            TOKEN_PATH.unlink()
        return "keychain"
    except Exception as exc:  # noqa: BLE001 — no keychain: fall back to the 600-mode file
        log.warning(
            "Keychain unavailable (%s: %s); Gmail credential written to %s with mode 600. "
            "This is the plan's original flow and an accepted exception to the secrets rule.",
            type(exc).__name__, exc, TOKEN_PATH.name,
        )
        TOKEN_PATH.write_text(payload, encoding="utf-8")
        TOKEN_PATH.chmod(0o600)
        return "file"


def load_credentials():
    """Load and refresh the stored credential. Never opens a browser."""
    import json

    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    raw, where = _read_token_json()
    try:
        info = json.loads(raw)
    except ValueError as exc:
        raise GmailAuthRequired(f"The stored Gmail token ({where}) is not valid JSON.") from exc
    creds = Credentials.from_authorized_user_info(info, SCOPES)

    if not creds.refresh_token:
        raise GmailAuthRequired(
            "The stored Gmail credential has no refresh token, so it will expire within the hour."
        )

    if creds.valid:
        return creds

    if creds.expired:
        try:
            creds.refresh(Request())
        except RefreshError as exc:
            # invalid_grant is usually a Google password change (which revokes Gmail-scoped
            # tokens by design) or an app still in Testing (7-day token lifetime).
            raise GmailAuthRequired(f"Gmail refresh was rejected ({exc}).") from exc
        store_token_json(creds.to_json())
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
