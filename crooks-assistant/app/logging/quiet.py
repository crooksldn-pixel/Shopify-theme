"""Keep the log readable: a line per question, tool and fault, not a line per poll."""

from __future__ import annotations

import logging

# What the tablet asks for on a timer. Success is the expected case and says nothing.
POLLED_PREFIXES = ("/state/", "/health", "/ping", "/static/", "/sw.js", "/manifest.webmanifest", "/favicon.ico")
QUIET_STATUSES = (200, 304)


class QuietPollsFilter(logging.Filter):
    """Drops uvicorn's access line for a poll that succeeded. During a turn the tablet asks
    /state every 400 ms and /health every 30 s; logged, they bury the lines that matter. A
    failure (any other status) is still logged, as is every request that is not a poll."""

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if isinstance(args, tuple) and len(args) == 5:
            path, status = args[2], args[4]
            if status in QUIET_STATUSES and isinstance(path, str) and path.startswith(POLLED_PREFIXES):
                return False
        return True


_FILTER = QuietPollsFilter()   # one instance, so repeated configuration does not stack copies


def quieten() -> None:
    """Silence what is only noise: successful polls, and httpx's line per outbound request
    (four of them per health check, one per voice line, all saying 200 OK)."""
    logging.getLogger("uvicorn.access").addFilter(_FILTER)
    logging.getLogger("httpx").setLevel(logging.WARNING)
