"""
Unit and integration tests for Four Corner MCP Server.
"""

import pytest
from four_corner.db.database import Database
from four_corner.server import (
    search_properties,
    get_floor_plan,
    get_pricing_breakdown,
    calculate_commute,
    verify_rera,
    compare_units,
)


@pytest.fixture(scope="module")
def test_db():
    db = Database()
    return db


def test_search_properties_budget_integrity(test_db):
    """Test that max_budget_cr strictly excludes properties above budget."""
    res = search_properties(max_budget_cr=1.5)
    assert res["status"] == "success"
    assert res["matched_count"] > 0
    for prop in res["properties"]:
        assert prop["total_price_cr"] <= 1.5, f"Property {prop['unit_id']} price {prop['total_price_cr']} exceeds 1.5 Cr!"


def test_search_properties_micro_market(test_db):
    """Test filtering by micro-market."""
    res = search_properties(micro_market="Kokapet")
    assert res["status"] == "success"
    for prop in res["properties"]:
        assert prop["micro_market"] == "Kokapet"


def test_search_properties_corner_and_sunlight(test_db):
    """Test filtering by corner unit with morning sunlight."""
    res = search_properties(corner_only=True, morning_sunlight_only=True)
    assert res["status"] == "success"
    assert res["matched_count"] > 0
    for prop in res["properties"]:
        assert prop["is_corner_unit"] is True


def test_get_floor_plan(test_db):
    """Test fetching room dimensions and carpet area efficiency."""
    res = get_floor_plan(unit_id="AKR-T3-1202")
    assert res["status"] == "success"
    plan = res["floor_plan"]
    assert plan["carpet_area_sqft"] == 1410
    assert plan["super_built_up_sqft"] == 1985
    assert plan["usable_efficiency_pct"] > 70.0
    assert len(plan["rooms"]) >= 4
    assert len(plan["balconies"]) >= 1
    assert any(b["morning_sunlight"] for b in plan["balconies"])


def test_get_pricing_breakdown(test_db):
    """Test transparent developer pricing breakdown with zero broker commission."""
    res = get_pricing_breakdown(unit_id="TRK-T2-1801")
    assert res["status"] == "success"
    breakdown = res["pricing_breakdown"]
    assert breakdown["broker_commission_inr"] == 0
    assert breakdown["total_in_crores"] > 0
    assert breakdown["true_cost_per_carpet_sqft_inr"] > breakdown["base_rate_per_sqft_inr"]


def test_calculate_commute(test_db):
    """Test rush-hour commute calculation to key IT hubs."""
    res = calculate_commute(project_id_or_name="My Home Akrida", destination_hub="Financial District")
    assert res["status"] == "success"
    assert len(res["commute_benchmarks"]) > 0
    c = res["commute_benchmarks"][0]
    assert c["rush_hour_morning_mins"] > c["non_peak_mins"]
    assert "Wipro" in c["key_intersections"][1] or len(c["key_intersections"]) > 0


def test_verify_rera(test_db):
    """Test official TS-RERA registration verification."""
    res = verify_rera(project_name_or_rera_id="P02400005128")
    assert res["status"] == "success"
    rera = res["rera_verification"]
    assert rera["project_name"] == "My Home Akrida"
    assert rera["escrow_account_compliant"] is True
    assert rera["litigations_reported"] == 0


def test_compare_units(test_db):
    """Test comparing multiple properties side-by-side."""
    res = compare_units(unit_ids=["AKR-T3-1202", "PRV-T7-1403"])
    assert res["status"] == "success"
    assert res["units_compared_count"] == 2
    for item in res["comparison"]:
        assert "carpet_area_sqft" in item
        assert "true_rate_per_carpet_sqft" in item


def test_rest_api_endpoints():
    """Test Starlette REST API endpoints for ChatGPT Actions."""
    from starlette.testclient import TestClient
    from four_corner.server import app

    client = TestClient(app)

    # Health check
    h = client.get("/health")
    assert h.status_code == 200
    assert h.json()["status"] == "healthy"

    # OpenAPI 3.1.0 schema
    o = client.get("/openapi.json")
    assert o.status_code == 200
    assert o.json()["openapi"] == "3.1.0"
    assert "/api/v1/properties/search" in o.json()["paths"]

    # Search endpoint
    s = client.get("/api/v1/properties/search?micro_market=Tellapur")
    assert s.status_code == 200
    assert s.json()["status"] == "success"

    # Floor plan endpoint
    fp = client.get("/api/v1/properties/floor-plan/AKR-T3-1202")
    assert fp.status_code == 200
    assert fp.json()["status"] == "success"

    # Pricing endpoint
    pr = client.get("/api/v1/properties/pricing/AKR-T3-1202")
    assert pr.status_code == 200
    assert pr.json()["status"] == "success"

    # Commute endpoint
    cm = client.get("/api/v1/commute/calculate?project_name=My+Home+Akrida")
    assert cm.status_code == 200
    assert cm.json()["status"] == "success"

    # RERA endpoint
    rr = client.get("/api/v1/rera/verify?query=P02400005128")
    assert rr.status_code == 200
    assert rr.json()["status"] == "success"

    # Compare endpoint
    cp = client.get("/api/v1/properties/compare?unit_ids=AKR-T3-1202,PRV-T7-1403")
    assert cp.status_code == 200
    assert cp.json()["status"] == "success"


def test_oauth_flow():
    """Test full OAuth 2.0 authorization, token exchange, and buyer tracking."""
    from starlette.testclient import TestClient
    from four_corner.server import app

    client = TestClient(app, follow_redirects=False)

    # 1. OAuth Discovery
    disc = client.get("/.well-known/oauth-authorization-server")
    assert disc.status_code == 200
    assert "/oauth/authorize" in disc.json()["authorization_endpoint"]

    # 2. Authorize Page
    auth_page = client.get("/oauth/authorize?client_id=chatgpt-plugin&redirect_uri=https://chatgpt.com/callback&state=test_state")
    assert auth_page.status_code == 200
    assert "Connect Four Corner with ChatGPT" in auth_page.text

    # 3. User submits login/signup
    post_res = client.post("/oauth/authorize", data={
        "name": "Sahith Test",
        "email": "test_buyer@fourcorner.in",
        "phone": "+91 99999 88888",
        "micro_market_pref": "Tellapur",
        "budget_max_cr": "2.0",
        "client_id": "chatgpt-plugin",
        "redirect_uri": "https://chatgpt.com/callback",
        "state": "test_state"
    })
    assert post_res.status_code == 302
    location = post_res.headers["location"]
    assert "https://chatgpt.com/callback" in location
    assert "code=fc_code_" in location
    code = location.split("code=")[1].split("&")[0]

    # 4. Exchange code for access token
    tok_res = client.post("/oauth/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": "chatgpt-plugin",
        "redirect_uri": "https://chatgpt.com/callback"
    })
    assert tok_res.status_code == 200
    tok_data = tok_res.json()
    assert tok_data["token_type"] == "Bearer"
    token = tok_data["access_token"]

    # 5. Access UserInfo with Bearer token
    u_res = client.get("/oauth/userinfo", headers={"Authorization": f"Bearer {token}"})
    assert u_res.status_code == 200
    assert u_res.json()["email"] == "test_buyer@fourcorner.in"

    # 6. Admin buyers check
    adm_res = client.get("/api/v1/admin/buyers")
    assert adm_res.status_code == 200
    assert adm_res.json()["total_buyers"] > 0


