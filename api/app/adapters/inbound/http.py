"""HTTP inbound (driving) adapter — translates requests into service calls and
domain errors into status codes. All business logic lives in the services; this
layer is deliberately thin."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from ...deps import (
    get_campaign_service,
    get_crew_service,
    get_member_service,
    get_pass_service,
    get_shop_service,
)
from ...domain.errors import CampaignNotFound, MemberNotFound, ShopNotFound
from ...domain.models import CampaignState, MemberRecord, Shop, ShopRecord
from ...services.campaign_service import CampaignService
from ...services.crew_service import CrewService
from ...services.member_service import MemberService
from ...services.pass_service import PassService
from ...services.shop_service import ShopService

router = APIRouter()


class RespondBody(BaseModel):
    action: str  # "approve" | "reject" | "kill"
    feedback: str | None = None


class EnrollBody(BaseModel):
    name: str = ""


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


@router.get("/shops/{shop_id}/pkpass")
def download_pkpass(
    shop_id: str,
    passes: PassService = Depends(get_pass_service),
) -> Response:
    """The shop's Apple Wallet pass. Signed when a cert is configured; a
    structurally-valid unsigned bundle otherwise (dev)."""
    try:
        issued = passes.issue_for_shop(shop_id)
    except ShopNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(
        content=issued.content,
        media_type=issued.media_type,
        headers={"Content-Disposition": f'attachment; filename="{issued.filename}"'},
    )


# ── members: end customers holding a shop's pass ──


@router.post(
    "/shops/{shop_id}/members", response_model=MemberRecord, status_code=201
)
def enroll_member(
    shop_id: str,
    body: EnrollBody,
    members: MemberService = Depends(get_member_service),
) -> MemberRecord:
    """Enrol a customer in the shop's pass — mints a unique serial number."""
    try:
        return members.enroll(shop_id, body.name)
    except ShopNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/shops/{shop_id}/members", response_model=list[MemberRecord])
def list_members(
    shop_id: str,
    members: MemberService = Depends(get_member_service),
) -> list[MemberRecord]:
    try:
        return members.list_for_shop(shop_id)
    except ShopNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/members/{member_id}", response_model=MemberRecord)
def get_member(
    member_id: str,
    members: MemberService = Depends(get_member_service),
) -> MemberRecord:
    try:
        return members.get(member_id)
    except MemberNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/members/{member_id}/stamp", response_model=MemberRecord)
def add_stamp(
    member_id: str,
    members: MemberService = Depends(get_member_service),
) -> MemberRecord:
    """+1 loyalty stamp for this customer's pass."""
    try:
        return members.add_stamp(member_id)
    except MemberNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/members/{member_id}/pkpass")
def download_member_pkpass(
    member_id: str,
    passes: PassService = Depends(get_pass_service),
) -> Response:
    """This customer's Apple Wallet pass (unique serial + current stamp count)."""
    try:
        issued = passes.issue_for_member(member_id)
    except (MemberNotFound, ShopNotFound) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(
        content=issued.content,
        media_type=issued.media_type,
        headers={"Content-Disposition": f'attachment; filename="{issued.filename}"'},
    )


# ── campaigns: crew drafts a launch campaign, founder approves via web ──


@router.post(
    "/shops/{shop_id}/campaign", response_model=CampaignState, status_code=202
)
async def start_campaign(
    shop_id: str,
    campaigns: CampaignService = Depends(get_campaign_service),
) -> CampaignState:
    """Kick off the crew. Returns immediately; poll GET /campaigns/{thread_id}
    until status is `awaiting_review`, then respond at the gate."""
    try:
        return await campaigns.start_for_shop(shop_id)
    except ShopNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/campaigns/{thread_id}", response_model=CampaignState)
def get_campaign(
    thread_id: str,
    campaigns: CampaignService = Depends(get_campaign_service),
) -> CampaignState:
    try:
        return campaigns.get(thread_id)
    except CampaignNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/campaigns/{thread_id}/respond", response_model=CampaignState)
async def respond_campaign(
    thread_id: str,
    body: RespondBody,
    campaigns: CampaignService = Depends(get_campaign_service),
) -> CampaignState:
    """Deliver the founder's decision (approve / reject+feedback / kill) to the gate."""
    try:
        return await campaigns.respond(thread_id, body.action, body.feedback)
    except CampaignNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
