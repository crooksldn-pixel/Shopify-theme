"""Non-secret configuration. Secrets are never read from here — see secrets/keychain.py."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CROOKS_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- transport ---
    host: str = "127.0.0.1"
    port: int = 8000

    # --- Shopify ---
    # The myshopify domain, not the storefront domain. Verified against the live store.
    shopify_shop_domain: str = "5wn03t-nm.myshopify.com"
    shopify_api_version: str = "2025-07"
    # "client_credentials" (Dev Dashboard app) or "static_token" (legacy shpat_ fallback, M6).
    shopify_auth_mode: str = "client_credentials"

    # --- speech ---
    whisper_url: str = "http://127.0.0.1:8910"
    whisper_model: str = "small.en"
    whisper_bin_dir: Path = Path.home() / "tools" / "whisper.cpp"

    # --- Claude ---
    claude_model: str = "sonnet"
    claude_cli_path: str = ""  # absolute path; resolved at startup if blank

    # --- behaviour ---
    tool_timeout_s: float = 8.0
    session_idle_timeout_s: int = 1800
    max_answer_chars: int = 700

    # --- paths ---
    kb_dir: Path = REPO_ROOT / "kb"
    bench_audio_dir: Path = REPO_ROOT / "bench" / "audio"
    bench_results_dir: Path = REPO_ROOT / "bench" / "results"
    log_dir: Path = REPO_ROOT / "logs"

    # --- dev toggles ---
    save_captures: bool = True
    # Keep only this many tablet recordings on disk. They are recordings of an office.
    max_saved_captures: int = 200


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
