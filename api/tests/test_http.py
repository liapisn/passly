"""HTTP inbound-adapter tests via TestClient, with fakes injected at the seam.

These check the transport concerns — status codes, request/response shapes,
domain-error mapping — without touching the real store singleton or the
framework.
"""

from __future__ import annotations

from .conftest import valid_shop


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "passly-api"}


def test_crew_info_uses_gateway(client):
    res = client.get("/crew/info")
    assert res.status_code == 200
    body = res.json()
    assert body["framework"] == "solo-founder-crew"
    assert body["roles"] == ["marketing", "product"]  # from FakeCrewGateway
    assert body["role_count"] == 2


def test_create_then_get_shop(client):
    created = client.post("/shops", json=valid_shop())
    assert created.status_code == 201
    shop_id = created.json()["id"]
    assert shop_id == "shop-1"

    fetched = client.get(f"/shops/{shop_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Καφέ Μαρία"


def test_list_shops(client):
    client.post("/shops", json=valid_shop())
    client.post("/shops", json=valid_shop())
    res = client.get("/shops")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_get_missing_shop_is_404(client):
    res = client.get("/shops/shop-404")
    assert res.status_code == 404


def test_bad_hex_colour_is_422(client):
    payload = valid_shop()
    payload["design"]["background_color"] = "green"
    res = client.post("/shops", json=payload)
    assert res.status_code == 422


# ── campaign flow (fake runner injected at the seam) ──


def _new_shop_id(client) -> str:
    return client.post("/shops", json=valid_shop()).json()["id"]


def test_start_campaign_pauses_at_gate(client):
    shop_id = _new_shop_id(client)
    res = client.post(f"/shops/{shop_id}/campaign")
    assert res.status_code == 202
    body = res.json()
    assert body["status"] == "awaiting_review"
    assert body["gate"]["options"] == ["approve", "reject", "kill"]


def test_start_campaign_unknown_shop_is_404(client):
    assert client.post("/shops/shop-404/campaign").status_code == 404


def test_approve_ships(client):
    shop_id = _new_shop_id(client)
    thread_id = client.post(f"/shops/{shop_id}/campaign").json()["thread_id"]
    res = client.post(f"/campaigns/{thread_id}/respond", json={"action": "approve"})
    assert res.status_code == 200
    assert res.json()["status"] == "shipped"
    assert res.json()["final_artifact"]


def test_reject_opens_next_gate(client):
    shop_id = _new_shop_id(client)
    thread_id = client.post(f"/shops/{shop_id}/campaign").json()["thread_id"]
    res = client.post(
        f"/campaigns/{thread_id}/respond",
        json={"action": "reject", "feedback": "warmer please"},
    )
    assert res.json()["status"] == "awaiting_review"
    assert res.json()["gate"]["turn"] == 2


def test_respond_unknown_campaign_is_404(client):
    res = client.post("/campaigns/camp-404/respond", json={"action": "approve"})
    assert res.status_code == 404


def test_get_unknown_campaign_is_404(client):
    assert client.get("/campaigns/camp-404").status_code == 404
