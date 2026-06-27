"""Passly API — FastAPI service bridging the Next.js UI and the solo-founder-crew framework.

P0 scaffold: a health endpoint and a `/crew/info` endpoint that imports the
framework, proving the dependency wiring works end to end. Real pass-issuance
(P1), the shop/designer flow (P2), and the crew + WebHITL flow (P3) land on
top of this.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import store
from .models import Shop, ShopRecord

app = FastAPI(
    title="Passly API",
    version="0.1.0",
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


@app.post("/shops", response_model=ShopRecord, status_code=201)
def create_shop(shop: Shop) -> ShopRecord:
    """Persist a shop and its pass design. P1 will sign the design into a .pkpass."""
    return store.create(shop)


@app.get("/shops", response_model=list[ShopRecord])
def list_shops() -> list[ShopRecord]:
    return store.list_all()


@app.get("/shops/{shop_id}", response_model=ShopRecord)
def get_shop(shop_id: str) -> ShopRecord:
    record = store.get(shop_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No shop {shop_id!r}")
    return record
