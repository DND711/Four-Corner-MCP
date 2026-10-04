"""
Tests for Buyer Readiness & Intent Scoring Engine (B-RISE).
"""

from four_corner.db.database import Database
from four_corner.auth import get_or_create_user, save_user_favorite, submit_developer_inquiry
from four_corner.scoring import compute_buyer_intent, log_buyer_event


def test_casual_browser_intent(tmp_path):
    db_file = tmp_path / "test_scoring.db"
    db = Database(db_path=db_file)

    user = get_or_create_user(db, "casual@example.com", "Casual User")
    intent = compute_buyer_intent(db, user["id"])

    assert intent["intent_score"] == 0
    assert intent["buyer_tier"] == "CASUAL_BROWSER"
    assert "Casual Browser" in intent["readiness_label"]


def test_serious_evaluator_intent(tmp_path):
    db_file = tmp_path / "test_scoring.db"
    db = Database(db_path=db_file)

    # 1. Registered buyer with phone and budget
    user = get_or_create_user(db, "serious@example.com", "Serious Buyer", "+919876543210", "Tellapur", 1.2, 3.0)
    
    # 2. Activity events
    log_buyer_event(db, user["id"], "get_pricing_breakdown", "Unit CND-T5-1602 pricing")
    log_buyer_event(db, user["id"], "get_floor_plan", "Unit CND-T5-1602 floor plan & sunlight")
    log_buyer_event(db, user["id"], "calculate_commute", "Commute to ADP Financial District")
    log_buyer_event(db, user["id"], "verify_rera_status", "Verify TS-RERA P02400005724")

    # 3. Actions
    save_user_favorite(db, user["id"], "CND-T5-1602", "Shortlisted")
    submit_developer_inquiry(db, user["id"], "Candeur Lakescape", "developer_direct_inquiry", "CND-T5-1602", "Developer allocation inquiry")

    intent = compute_buyer_intent(db, user["id"])
    assert intent["intent_score"] >= 65
    assert intent["buyer_tier"] in ["SERIOUS_EVALUATOR", "TRANSACTION_READY"]
    assert intent["total_saved_units"] == 1
    assert intent["total_inquiries"] == 1
