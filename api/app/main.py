"""Passly API — application entry point.

A thin composition layer: build the FastAPI app, apply CORS, mount the HTTP
inbound adapter. All wiring of adapters into services lives in `deps.py`; all
behaviour lives in `services/` and `domain/`. See the hexagonal layout:

    domain/    entities + ports (Protocols) + errors   — framework-free core
    services/  use cases, depend only on ports
    adapters/  inbound (http) + outbound (memory repo, crew gateway)
    deps.py    composition root (which adapter backs which port)
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .adapters.inbound.http import router


def create_app() -> FastAPI:
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
    app.include_router(router)
    return app


app = create_app()
