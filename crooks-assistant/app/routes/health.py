"""Per-subsystem health, so the tablet can name what is broken rather than saying "error"."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request

router = APIRouter()

VERSION = "0.1.0"


@router.get("/health")
async def health(request: Request) -> dict:
    runtime = request.app.state.runtime
    checks: dict[str, dict] = {}

    async def check(name: str, coro):
        try:
            ok, detail = await asyncio.wait_for(coro, timeout=6)
        except TimeoutError:
            ok, detail = False, "check timed out"
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        checks[name] = {"ok": ok, "detail": detail}

    await asyncio.gather(
        check("claude", runtime.provider.health()),
        check("whisper", runtime.whisper.health()),
        check("shopify", runtime.shopify.health()),
        check("gmail", asyncio.to_thread(runtime.gmail.health)),
    )

    # The plan's M3 failure check: Core ML build succeeds but the .mlmodelc is missing, and
    # everything runs twice as slowly with no error. Say so here so it cannot go unnoticed.
    bin_dir = runtime.settings.whisper_bin_dir
    coreml = bin_dir / "models" / f"ggml-{runtime.settings.whisper_model}-encoder.mlmodelc"
    if checks["whisper"]["ok"]:
        checks["whisper"]["detail"] += (
            f" · Core ML encoder {'present' if coreml.exists() else 'MISSING (GPU only, ~2x slower)'}"
        )

    checks["knowledge_base"] = {
        "ok": not runtime.kb.empty,
        "detail": f"{len(runtime.kb.files)} file(s), {runtime.kb.chars} chars",
    }
    checks["terminology"] = {
        "ok": len(runtime.normaliser.catalogue) > 0,
        "detail": f"{len(runtime.normaliser.catalogue)} term(s)",
    }

    return {
        # Degraded, not down: Shopify being unreachable should not make the page say the
        # backend is offline, because Gmail and the knowledge base still work.
        "status": "ok" if all(c["ok"] for c in checks.values()) else "degraded",
        "version": VERSION,
        "uptime_s": round(runtime.uptime_s, 1),
        "sessions": runtime.sessions.count(),
        "checks": checks,
    }
