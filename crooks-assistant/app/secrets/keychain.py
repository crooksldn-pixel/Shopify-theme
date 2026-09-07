"""Thin keyring wrapper. Every secret in this project is read through here and nowhere else.

Secrets are written once by scripts/set_secrets.py at an interactive local prompt. They are
never written to a file, never committed, never echoed, and never included in a log line.
"""

from __future__ import annotations

SERVICE = "crooks-assistant"

# The complete set of secrets this application will ever hold. Anything not on this list
# is a bug or a mistake, so lookups are validated against it.
KNOWN_KEYS = (
    "claude_oauth_token",
    "shopify_client_id",
    "shopify_client_secret",
    "shopify_static_token",  # legacy shpat_ fallback (M6 failure path only)
)


class SecretMissing(RuntimeError):
    """Raised when a required secret has not been stored in the Keychain."""

    def __init__(self, key: str) -> None:
        super().__init__(
            f"Secret {key!r} is not in the {SERVICE} keychain entry. "
            f"Store it with: python scripts/set_secrets.py {key}"
        )
        self.key = key


def _validate(key: str) -> None:
    if key not in KNOWN_KEYS:
        raise ValueError(f"Unknown secret key {key!r}. Known keys: {', '.join(KNOWN_KEYS)}")


class KeychainUnavailable(SecretMissing):
    """No usable keyring backend — Linux without a secret service, or a macOS process running
    outside a login session (launchd before login, an SSH shell). Treated as "secret missing"
    so callers fall back or fail with a message that names the real cause."""

    def __init__(self, key: str, cause: Exception) -> None:
        RuntimeError.__init__(
            self,
            f"Secret {key!r} could not be read: the keychain is unavailable to this process "
            f"({type(cause).__name__}: {cause}). On macOS this usually means the process is "
            "running outside your login session.",
        )
        self.key = key


def get(key: str) -> str:
    """Return a secret, raising SecretMissing if absent. Never logs the value."""
    _validate(key)
    import keyring

    try:
        value = keyring.get_password(SERVICE, key)
    except Exception as exc:  # noqa: BLE001 — every keyring backend raises its own type
        raise KeychainUnavailable(key, exc) from exc
    if not value:
        raise SecretMissing(key)
    return value


def get_optional(key: str) -> str | None:
    """Return a secret or None. Used where a credential is a documented fallback."""
    try:
        return get(key)
    except SecretMissing:
        return None


def set_secret(key: str, value: str) -> None:
    _validate(key)
    if not value.strip():
        raise ValueError("Refusing to store an empty secret.")
    import keyring

    keyring.set_password(SERVICE, key, value)


def delete(key: str) -> None:
    _validate(key)
    import keyring

    try:
        keyring.delete_password(SERVICE, key)
    except Exception:  # noqa: BLE001 — keyring raises backend-specific errors for "absent"
        pass


def present(key: str) -> bool:
    """True if the secret exists. Deliberately returns a bool, never the value."""
    return get_optional(key) is not None
