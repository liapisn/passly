"""Platform-neutral result of issuing a pass.

Apple returns `.pkpass` bytes (a file download); a future Google Wallet issuer
would return a "Save to Google Wallet" link. Both fit here — the transport
layer just honours `media_type` / `filename` (or treats an issuer that returns
a URL accordingly).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IssuedPass:
    content: bytes
    media_type: str
    filename: str
    platform: str  # "apple" | "google" | …
