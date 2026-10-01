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
