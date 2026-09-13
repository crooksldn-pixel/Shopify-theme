# Instagram agent skills

Vendored from [Jakeschincariol/instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill)
at commit `d03c56bb598be770c60b201f94237e5d1a4268a6`. MIT licensed; see `LICENSE` in this folder.

13 skills, invoked as `/ig-reel`, `/ig-caption`, `/ig-viral`, `/ig-carousel`,
`/ig-story`, `/ig-profile`, `/ig-plan`, `/ig-human`, `/ig-comment`,
`/ig-reply`, `/ig-dm`, `/ig-repurpose`, `/ig-audit`.

Six Python tools run locally on stdlib only, with no network calls:
`ig-reel/hookscore.py`, `ig-reel/beats.py`, `ig-caption/caption.py`,
`ig-human/humanize.py`, `ig-human/detect.py`, `ig-viral/swipe.py`.
They exit non-zero when a draft fails its own quality gate, which is by design.

`ig-viral/swipe.py` reads `../ig-reel/hooks.json`, so keep the folders together.

## Before first use

Fill in the voice profile at `.claude/instagram/voice.md`. Every skill reads it,
and the skills look for it at `~/.claude/instagram/voice.md`, so copy it there:

```bash
mkdir -p ~/.claude/instagram && cp .claude/instagram/voice.md ~/.claude/instagram/
```

These skills write drafts. Nothing posts to Instagram.
