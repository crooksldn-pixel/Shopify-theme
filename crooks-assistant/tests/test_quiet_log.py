"""The log is for reading: a line per question, tool and fault, not per poll."""

from __future__ import annotations

import logging

from app.logging.quiet import QuietPollsFilter, quieten


def _access(path: str, status: int) -> logging.LogRecord:
    return logging.LogRecord(
        "uvicorn.access", logging.INFO, __file__, 1, '%s - "%s %s HTTP/%s" %d',
        ("100.1.1.1:0", "GET", path, "1.1", status), None,
    )


def test_successful_polls_are_dropped_and_everything_else_is_kept():
    f = QuietPollsFilter()
    assert not f.filter(_access("/state/abc", 200))
    assert not f.filter(_access("/health", 200))
    assert not f.filter(_access("/health?fresh=1", 200))
    assert not f.filter(_access("/static/app.js", 304))
    assert f.filter(_access("/turn", 200)), "a question is always logged"
    assert f.filter(_access("/speak", 200))
    assert f.filter(_access("/health", 500)), "a failing poll is news"
    assert f.filter(_access("/state/abc", 403))
    plain = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1, "started", (), None)
    assert f.filter(plain)


def test_quieten_is_idempotent_and_silences_httpx_chatter():
    quieten()
    quieten()
    access = logging.getLogger("uvicorn.access")
    assert sum(isinstance(x, QuietPollsFilter) for x in access.filters) == 1
    assert logging.getLogger("httpx").level == logging.WARNING
