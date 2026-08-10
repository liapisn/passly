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

from pathlib import Path

from dotenv import load_dotenv

# Load api/.env before anything reads os.environ (signing config lives there).
# No-op if the file is absent (e.g. CI); never raises.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from .adapters.inbound.http import router  # noqa: E402


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
