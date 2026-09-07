"""Small operational endpoints: voice list metadata and knowledge-base reload."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/voices")
async def voices() -> dict:
    """The voice list itself comes from the browser — only the browser knows what is installed.
    This endpoint carries the guidance the picker shows alongside it."""
    return {
        "preferred_langs": ["en-GB", "en"],
        "guidance": (
            "Prefer a voice whose lang is en-GB and whose localService is true — a local voice "
            "keeps working when the network does not. If every voice shows localService false, "
            "install the en-GB voice data on the tablet: Settings, General management, "
            "Text-to-speech, Install voice data."
        ),
    }


@router.post("/reload-kb")
async def reload_kb(request: Request) -> dict:
    runtime = request.app.state.runtime
    kb = runtime.reload_kb()
    return {"reloaded": True, "files": kb.files, "chars": kb.chars}


@router.get("/tools")
async def tools() -> dict:
    """What the assistant can do, and at what tier. Useful when a refusal is surprising."""
    from app.tools.registry import all_specs

    return {
        "tools": [
            {"name": s.name, "tier": s.tier.value, "description": s.description}
            for s in all_specs()
        ]
    }
