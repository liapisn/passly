"""EmailSender adapters.

`FakeEmailSender` records sends in memory (dev/CI, and a test double) — nothing
leaves the process. `ResendEmailSender` posts to the Resend API when a key is
configured. `httpx` is imported lazily so dev/CI need neither it exercised nor
a key present.
"""

from __future__ import annotations

import logging

_log = logging.getLogger("passly.email")


class FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    def send(self, *, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})
        _log.info("FakeEmailSender: NOT sending (no RESEND_API_KEY) — would email %s", to)


class ResendEmailSender:
    def __init__(self, api_key: str, *, from_addr: str = "onboarding@resend.dev") -> None:
        self._key = api_key
        self._from = from_addr

    def send(self, *, to: str, subject: str, body: str) -> None:
        import httpx

        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {self._key}"},
            json={"from": self._from, "to": [to], "subject": subject, "html": body},
            timeout=10,
        )
        # Surface Resend's error body (e.g. "can only send to your own address").
        if resp.status_code >= 400:
            raise RuntimeError(f"Resend {resp.status_code}: {resp.text}")
        _log.info("Resend: accepted email to %s (from %s)", to, self._from)
