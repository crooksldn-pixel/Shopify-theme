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
    # Who may ask, as Tailscale logins ("you@example.com, partner@example.com"). Empty means
    # anyone on the tailnet — it is the owner's own private network. Set it and every request
    # proxied by `tailscale serve` from another login is refused; requests made on the Mac
    # itself carry no login and are always allowed.
    allowed_logins: str = ""

    # --- Shopify ---
    # The myshopify domain, not the storefront domain. Verified against the live store.
    shopify_shop_domain: str = "5wn03t-nm.myshopify.com"
    shopify_api_version: str = "2025-07"
    # "client_credentials" (Dev Dashboard app) or "static_token" (legacy shpat_ fallback, M6).
    shopify_auth_mode: str = "client_credentials"

    # --- speech ---
    # Which recogniser runs first: "scribe" (ElevenLabs, the default) or "whisper" (local only).
    # Whisper is the automatic fallback either way and is never switched off by this setting.
    stt_primary: str = "scribe"
    scribe_model: str = "scribe_v2"
    scribe_language: str = "eng"  # ISO-639-3, as the ElevenLabs API expects
    scribe_timeout_s: float = 20.0
    # Bias Scribe with the live/seed product catalogue. Product words only — never customers.
    scribe_keyterms: bool = True
    # ElevenLabs bills a 20-second minimum for requests carrying 100 or more keyterms.
    scribe_max_keyterms: int = 99
    # After a rejected key or an exhausted account, stop calling Scribe for this long and go
    # straight to Whisper, so a broken account does not add a round trip to every sentence.
    scribe_cooldown_s: float = 300.0
    elevenlabs_base_url: str = "https://api.elevenlabs.io/v1"

    # --- the assistant's voice (ElevenLabs text-to-speech) ---
    # Off falls the tablet back to Android's own speechSynthesis, which is what it used before.
    tts_enabled: bool = True
    # "Derek - Fun & Energetic", from the ElevenLabs library — used by id, without being added
    # to the account. Voice settings are left at his own defaults; there is nothing to tune
    # here until he has been heard on the tablet's speaker. `make voice` hears a change here.
    tts_voice_id: str = "Q0Et7LOU7VpeoeCRQAVS"
    tts_voice_name: str = "Derek"
    tts_model: str = "eleven_flash_v2_5"  # the low-latency model; this is a conversation
    # ~16 kB/s. The 32 kbps stream this replaced was audibly compressed on the tablet
    # speaker, and four times the bytes is nothing next to the generation time.
    tts_output_format: str = "mp3_44100_128"
    # ElevenLabs answers the first byte of an MP3 within a second or two; a voice that has
    # not started by now is a voice that is not coming, and Android's should take over.
    tts_timeout_s: float = 10.0
    # Start synthesising an answer the moment /turn knows it, so it is generating while the
    # tablet asks for it. Off means /speak synthesises on request, as it did before.
    tts_prefetch: bool = True
    # Longer than one answer can be (max_answer_chars is 700) with room for the spoken forms,
    # which are longer than the digits they replace.
    tts_max_chars: int = 1200
    tts_cooldown_s: float = 300.0

    whisper_url: str = "http://127.0.0.1:8910"
    whisper_model: str = "small.en"
    whisper_bin_dir: Path = Path.home() / "tools" / "whisper.cpp"
    # How much audio to keep either side of detected speech. whisper.cpp's default is 30 ms,
    # which shaves the soft start of a first word; 200 ms keeps it.
    whisper_vad_pad_ms: int = 200

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
