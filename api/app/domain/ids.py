"""Short, URL-safe, non-guessable ids (nanoid-style) — not sequential numbers.

`shop_7h2p9kqm3x4a`, `mem_…`, `psly_…` (pass serial). Prefixed so they stay
human-scannable, random body so counts don't leak and ids aren't enumerable.
Crockford base32 alphabet (no i/l/o/u) via stdlib `secrets` — no dependency.
"""

from __future__ import annotations

import secrets

_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"


def small_id(prefix: str, length: int = 12) -> str:
    body = "".join(secrets.choice(_ALPHABET) for _ in range(length))
    return f"{prefix}_{body}"
