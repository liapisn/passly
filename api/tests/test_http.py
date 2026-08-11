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
    assert shop_id.startswith("shop_")  # non-sequential smallId

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


# ── pkpass download ──


def test_download_pkpass(client):
    shop_id = client.post("/shops", json=valid_shop()).json()["id"]
    res = client.get(f"/shops/{shop_id}/pkpass")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/vnd.apple.pkpass"
    assert res.content[:2] == b"PK"  # it's a zip


def test_download_pkpass_unknown_shop_is_404(client):
    assert client.get("/shops/shop-404/pkpass").status_code == 404


# ── members ──


def _new_shop(client) -> str:
    return client.post("/shops", json=valid_shop()).json()["id"]


def test_enroll_and_list_members(client):
    shop_id = _new_shop(client)
    a = client.post(
        f"/shops/{shop_id}/members", json={"name": "Νίκος", "email": "nikos@example.com"}
    )
    assert a.status_code == 201
    assert a.json()["serial_number"]
    assert a.json()["stamps"] == 0
    assert a.json()["email"] == "nikos@example.com"
    client.post(
        f"/shops/{shop_id}/members", json={"name": "Μαρία", "email": "maria@example.com"}
    )
    listed = client.get(f"/shops/{shop_id}/members").json()
    assert len(listed) == 2


def test_same_email_does_not_duplicate(client):
    shop_id = _new_shop(client)
    body = {"name": "Νίκος", "email": "nikos@example.com"}
    first = client.post(f"/shops/{shop_id}/members", json=body).json()
    again = client.post(f"/shops/{shop_id}/members", json=body).json()
    assert again["id"] == first["id"]
    assert len(client.get(f"/shops/{shop_id}/members").json()) == 1


def test_enroll_bad_email_is_422(client):
    shop_id = _new_shop(client)
    r = client.post(f"/shops/{shop_id}/members", json={"name": "X", "email": "nope"})
    assert r.status_code == 422


def test_enroll_unknown_shop_is_404(client):
    r = client.post("/shops/shop-404/members", json={"name": "X", "email": "x@example.com"})
    assert r.status_code == 404


def test_add_stamp(client):
    shop_id = _new_shop(client)
    mid = client.post(
        f"/shops/{shop_id}/members", json={"name": "Νίκος", "email": "nikos@example.com"}
    ).json()["id"]
    r = client.post(f"/members/{mid}/stamp")
    assert r.status_code == 200
    assert r.json()["stamps"] == 1


def test_member_pkpass_download(client):
    shop_id = _new_shop(client)
    mid = client.post(
        f"/shops/{shop_id}/members", json={"name": "Νίκος", "email": "nikos@example.com"}
    ).json()["id"]
    r = client.get(f"/members/{mid}/pkpass")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.apple.pkpass"
    assert r.content[:2] == b"PK"


def test_member_endpoints_404(client):
    assert client.get("/members/mem-404").status_code == 404
    assert client.post("/members/mem-404/stamp").status_code == 404
    assert client.get("/members/mem-404/pkpass").status_code == 404
