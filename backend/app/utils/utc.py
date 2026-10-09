"""Say which timezone a timestamp is in, on the way out.

Every datetime column in this system is written with `datetime.utcnow()`
(`models/deal.py:36` and its dozen siblings), so it is naive UTC. The API used
to serialise them as `"2026-09-12T08:49:20"` -- no `Z`, no offset -- and the
browser is then entitled to read that as local time, because that is what the
ECMAScript specification says an offset-less date-time means. On a UTC+8 screen
the UTC digits were printed verbatim, so a card created at 16:49 in Kuala Lumpur
read 08:49. Nothing was ever converted; the instant was simply lost in transit.

**Why at the wire and not at the source.** This codebase has no
`response_model` anywhere: `routers/` hand-build their payloads and
`utils/response.py` serialises them with `json.dumps`. The timestamps are
stringified in about twenty different services before they ever reach it. Adding
`+ "Z"` to each is twenty chances to miss one, and two of them
(`routers/messages.py:188`, `services/whatsapp_service.py:385`) have already
been fixed by hand -- doing it again there would produce a double `Z`.

One pass at the single point every response goes through cannot miss one, and is
idempotent, so the two already-fixed sites need no special treatment and no
coordination.

**Why `fullmatch`.** The whole string must be a naive ISO timestamp and nothing
else. A deal title, a note, an address -- anything with other characters around
it -- is not touched. A field whose entire value is a timestamp is a timestamp.

`fullmatch` rather than anchors on the pattern: with `re.match` a leading `^` is
silently redundant, so only the `$` would have been load-bearing, and a reader
cannot tell which half is doing the work.

Three properties fall out of the pattern rather than out of anybody remembering
them:

- **Idempotent.** A value that already carries `Z` or `+08:00` does not match.
- **Dates are safe.** `"2026-09-12"` has no `T`, so `last_contact` and
  `due_date` are untouched. Stamped as `"...T00:00:00Z"` they would read as the
  previous day on any browser west of Greenwich.
- **Times of day are safe.** `"08:49:20"` has no date, so it does not match.
"""

from __future__ import annotations

import re
from typing import Any

# A naive ISO datetime and nothing else. Both `T` and space separators, because
# not every payload here went through `.isoformat()`.
NAIVE_ISO_DATETIME = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?")


def mark_utc(value: Any) -> Any:
    """Append `Z` to every naive ISO timestamp in an already-JSON-able value.

    Recurses through dicts and lists. Everything else is returned untouched --
    including strings that merely contain a timestamp rather than being one.
    """
    if isinstance(value, str):
        return value + "Z" if NAIVE_ISO_DATETIME.fullmatch(value) else value
    if isinstance(value, dict):
        return {key: mark_utc(item) for key, item in value.items()}
    if isinstance(value, list):
        return [mark_utc(item) for item in value]
    return value
