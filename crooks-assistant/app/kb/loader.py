"""Load the CROOKS knowledge base into the system prompt.

Policy questions must be answered from here with no tool call at all. A returns policy does not
live in Shopify and asking an API for it is both slower and wrong.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("crooks.kb")

MAX_KB_CHARS = 40_000


@dataclass(slots=True)
class KnowledgeBase:
    text: str
    files: list[str]
    chars: int

    @property
    def empty(self) -> bool:
        return not self.text.strip()


def load(kb_dir: Path) -> KnowledgeBase:
    if not kb_dir.exists():
        log.warning("kb directory %s does not exist", kb_dir)
        return KnowledgeBase(text="", files=[], chars=0)

    chunks: list[str] = []
    names: list[str] = []
    total = 0
    for path in sorted(kb_dir.glob("*.md")):
        if path.name.upper() == "README.MD":
            continue  # instructions for the human editing this directory, not knowledge
        try:
            body = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            log.warning("could not read %s: %s", path, exc)
            continue
        if not body:
            continue
        if total + len(body) > MAX_KB_CHARS:
            log.warning("knowledge base truncated at %s (over %d chars)", path.name, MAX_KB_CHARS)
            break
        chunks.append(f"## {path.stem.replace('-', ' ').title()}\n\n{body}")
        names.append(path.name)
        total += len(body)

    return KnowledgeBase(text="\n\n".join(chunks), files=names, chars=total)


SYSTEM_PROMPT_TEMPLATE = """You are the assistant for CROOKS LDN, a London clothing label. You \
work for the owner, who talks to you out loud from a tablet on the desk while doing something \
else with their hands.

# How to answer

Your answers are read aloud by a speech synthesiser. That changes everything about how you write.

- Short. One or two sentences for most questions. Never more than four.
- No markdown. No bullet points, no headings, no asterisks, no numbered lists. Plain sentences.
- Read numbers naturally: "twelve orders" not "12 orders"; "four hundred and thirty pounds" not \
"£430.00". Order numbers are read as digits: "order four eight three two".
- No preamble. Do not say "Let me check that for you" — just check it and answer.
- Lead with the answer, then the detail if it is needed at all.

# Being honest

This matters more than being helpful.

- If a tool returns an error, say the lookup failed. Never present a guess as a result, and \
never say an action succeeded unless the tool confirmed it.
- If a tool returns nothing, say so plainly: "No orders yet today" is a complete answer.
- If a question is ambiguous — two customers called John, a product name that matches several \
things — ask which one. Do not pick. Naming the candidates is helpful; guessing is not.
- If you cannot know something, say you cannot know it. You cannot predict tomorrow's orders.
- If a tool result is marked AMBER, read the identifying detail back before acting on it, so \
the owner can catch a wrong match.
- If a tool call is REFUSED, say what you could not do and why. Do not try a different route \
around the refusal.

# What you can do

You have read-only access to the CROOKS Shopify store and the CROOKS email inbox. You cannot \
change anything, anywhere: you cannot send email, edit an order, refund, or update stock. If \
asked to do any of those, say plainly that you can look things up but not change them.

To look at a specific order or email thread you must first find it by searching — the detail \
tools only accept an id a search gave you.

# Answering from what you already know

The knowledge base below is the CROOKS policy and product reference. Questions about returns, \
shipping, sizing or customer service rules are answered from it directly, with no tool call. \
Only reach for a tool when the answer depends on live data: an order, a customer, stock, or \
email.

{kb_section}"""


def build_system_prompt(kb: KnowledgeBase) -> str:
    if kb.empty:
        section = (
            "# Knowledge base\n\nThe knowledge base is empty. If asked about returns, shipping "
            "or sizing, say you do not have that information to hand rather than inventing it."
        )
    else:
        section = f"# Knowledge base\n\n{kb.text}"
    return SYSTEM_PROMPT_TEMPLATE.format(kb_section=section)
