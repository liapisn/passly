"""Passly API — FastAPI service bridging the Next.js UI and the solo-founder-crew framework.

P0 scaffold: a health endpoint and a `/crew/info` endpoint that imports the
framework, proving the dependency wiring works end to end. Real pass-issuance
(P1), the shop/designer flow (P2), and the crew + WebHITL flow (P3) land on
top of this.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Passly API",
    version="0.0.0",
    summary="Wallet passes + AI marketing for Greek SMBs — thesis demo backend.",
)

# Next.js dev server runs on :3000; allow it during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by the web app to confirm the API is up."""
    return {"status": "ok", "service": "passly-api"}


@app.get("/crew/info")
def crew_info() -> dict[str, object]:
    """Prove the solo-founder-crew dependency is importable and report the role catalogue.

    This is the P0 smoke check: if this returns the six roles, the
    Next.js → FastAPI → solo-founder-crew chain is wired correctly.
    """
    from solo_founder_crew.roles_library import ROLE_LIBRARY

    return {
        "framework": "solo-founder-crew",
        "roles": sorted(ROLE_LIBRARY.keys()),
        "role_count": len(ROLE_LIBRARY),
    }
