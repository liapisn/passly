"""HTTP inbound (driving) adapter — translates requests into service calls and
domain errors into status codes. All business logic lives in the services; this
layer is deliberately thin."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ...deps import get_crew_service, get_shop_service
from ...domain.errors import ShopNotFound
from ...domain.models import Shop, ShopRecord
from ...services.crew_service import CrewService
from ...services.shop_service import ShopService

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by the web app to confirm the API is up."""
    return {"status": "ok", "service": "passly-api"}


@router.get("/crew/info")
def crew_info(
    crew: CrewService = Depends(get_crew_service),
) -> dict[str, object]:
    """Smoke check: proves the framework is reachable behind the CrewGateway port."""
    roles = crew.role_catalogue()
    return {
        "framework": "solo-founder-crew",
        "roles": roles,
        "role_count": len(roles),
    }


@router.post("/shops", response_model=ShopRecord, status_code=201)
def create_shop(
    shop: Shop,
    shops: ShopService = Depends(get_shop_service),
) -> ShopRecord:
    """Persist a shop and its pass design. P1 will sign the design into a .pkpass."""
    return shops.create_shop(shop)


@router.get("/shops", response_model=list[ShopRecord])
def list_shops(
    shops: ShopService = Depends(get_shop_service),
) -> list[ShopRecord]:
    return shops.list_shops()


@router.get("/shops/{shop_id}", response_model=ShopRecord)
def get_shop(
    shop_id: str,
    shops: ShopService = Depends(get_shop_service),
) -> ShopRecord:
    try:
        return shops.get_shop(shop_id)
    except ShopNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
