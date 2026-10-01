"""
Four Corner Buyer Readiness & Intent Scoring Engine (B-RISE).
Quantifies buyer purpose, commitment, and purchasing stage across 5 dimensions.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime


def compute_buyer_intent(db, user_id: str) -> Dict[str, Any]:
    """
    Computes a 100-point multi-dimensional buyer intent score for a user:
      1. Financial Precision (25 pts)
      2. Commute & Workplace Alignment (20 pts)
      3. Architectural & Livability Specificity (20 pts)
      4. Legal Due Diligence & RERA Rigor (15 pts)
      5. Commitment & Action Signals (20 pts)
    """
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # 1. Fetch user profile
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        raw_user = cursor.fetchone()
        if not raw_user:
            return {"intent_score": 0, "buyer_tier": "CASUAL_BROWSER", "breakdown": {}}
        user = dict(raw_user)

        # 2. Fetch saved units
        cursor.execute("SELECT COUNT(*) as count FROM user_saved_units WHERE user_id = ?", (user_id,))
        saved_row = cursor.fetchone()
        saved_count = dict(saved_row).get("count", 0) if saved_row else 0

        # 3. Fetch inquiries
        cursor.execute("SELECT * FROM user_inquiries WHERE user_id = ?", (user_id,))
        inquiries = [dict(r) for r in cursor.fetchall()]
        inquiry_count = len(inquiries)

        # 4. Fetch audit log activities
        cursor.execute("SELECT * FROM user_audit_logs WHERE user_id = ?", (user_id,))
        audit_logs = [dict(l) for l in cursor.fetchall()]

    # Analyze audit events
    tools_used = [log.get("tool_name") for log in audit_logs]
    
    # ----------------------------------------------------
    # Dimension 1: Financial Precision (Max 25 pts)
    # ----------------------------------------------------
    fin_score = 0
    # Explicit budget ceiling defined in profile or search
    if user.get("budget_max_cr") and float(user["budget_max_cr"]) > 0:
        fin_score += 5
    # Inspecting unbundled builder cost sheets
    pricing_views = tools_used.count("get_pricing_breakdown")
    if pricing_views >= 1:
        fin_score += 8
    if pricing_views >= 2:
        fin_score += 7
    # Multi-unit comparisons or budget constraints
    if "compare_units" in tools_used:
        fin_score += 5
    fin_score = min(25, fin_score)

    # ----------------------------------------------------
    # Dimension 2: Commute & Workplace Alignment (Max 20 pts)
    # ----------------------------------------------------
    commute_score = 0
    commute_views = tools_used.count("calculate_commute")
    if commute_views >= 1:
        commute_score += 8
    if commute_views >= 2:
        commute_score += 6
    # Workplace check (e.g. ADP, Financial District)
    has_workplace_query = any("adp" in str(l.get("query_summary", "")).lower() for l in audit_logs)
    if has_workplace_query or commute_views >= 1:
        commute_score += 6
    commute_score = min(20, commute_score)

    # ----------------------------------------------------
    # Dimension 3: Architectural & Livability Specificity (Max 20 pts)
    # ----------------------------------------------------
    arch_score = 0
    fp_views = tools_used.count("get_floor_plan")
    if fp_views >= 1:
        arch_score += 6
    if fp_views >= 2:
        arch_score += 4
    # Specific livability filters (BHK, sunlight, corner orientation)
    if user.get("bhk_pref"):
        arch_score += 5
    has_sunlight_or_corner = any(
        "sunlight" in str(l.get("query_summary", "")).lower() or "corner" in str(l.get("query_summary", "")).lower()
        for l in audit_logs
    )
    if has_sunlight_or_corner:
        arch_score += 5
    arch_score = min(20, arch_score)

    # ----------------------------------------------------
    # Dimension 4: Legal Due Diligence & RERA Rigor (Max 15 pts)
    # ----------------------------------------------------
    legal_score = 0
    rera_views = tools_used.count("verify_rera_status")
    if rera_views >= 1:
        legal_score += 8
    if rera_views >= 2:
        legal_score += 4
    if any("escrow" in str(l.get("query_summary", "")).lower() for l in audit_logs):
        legal_score += 3
    legal_score = min(15, legal_score)

    # ----------------------------------------------------
    # Dimension 5: Commitment & Action Signals (Max 20 pts)
    # ----------------------------------------------------
    action_score = 0
    # Verified login with phone number
    if user.get("phone"):
        action_score += 5
    # Portfolio shortlisting
    if saved_count >= 1:
        action_score += 5
    if saved_count >= 2:
        action_score += 4
    # Direct builder inquiry / site visit request
    if inquiry_count >= 1:
        action_score += 6
    action_score = min(20, action_score)

    # Total Score (0 - 100)
    total_score = fin_score + commute_score + arch_score + legal_score + action_score

    # Determine CRM Tier
    if total_score >= 75:
        tier = "TRANSACTION_READY"
        readiness_label = "High-Intent Buyer (Ready to buy within 30 days)"
        recommended_action = "Priority site visit assignment with zero broker commission"
    elif total_score >= 50:
        tier = "SERIOUS_EVALUATOR"
        readiness_label = "Serious Evaluator (Evaluating blueprints and cost sheets)"
        recommended_action = "Provide architectural blueprints, payment milestones, and bank loan pre-clearance"
    elif total_score >= 25:
        tier = "WARM_RESEARCHER"
        readiness_label = "Warm Researcher (Exploring micro-markets and budgets)"
        recommended_action = "Share micro-market price appreciation trends and neighborhood infrastructure updates"
    else:
        tier = "CASUAL_BROWSER"
        readiness_label = "Casual Browser (Market curiosity)"
        recommended_action = "Standard AI automated guidance; no sales desk dispatch needed"

    breakdown = {
        "financial_precision": {"score": fin_score, "max": 25},
        "commute_alignment": {"score": commute_score, "max": 20},
        "architectural_depth": {"score": arch_score, "max": 20},
        "legal_due_diligence": {"score": legal_score, "max": 15},
        "commitment_signals": {"score": action_score, "max": 20},
    }

    result = {
        "user_id": user_id,
        "intent_score": total_score,
        "buyer_tier": tier,
        "readiness_label": readiness_label,
        "recommended_action": recommended_action,
        "breakdown": breakdown,
        "total_saved_units": saved_count,
        "total_inquiries": inquiry_count,
        "total_audit_events": len(audit_logs)
    }

    # Persist updated score into database
    try:
        with db.get_connection() as conn:
            conn.execute(
                """
                UPDATE users 
                SET intent_score = ?, buyer_tier = ?, intent_breakdown = ?, last_activity_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (total_score, tier, json.dumps(breakdown), user_id)
            )
            conn.commit()
    except Exception:
        pass

    return result


def log_buyer_event(db, user_id: Optional[str], tool_name: str, query_summary: Optional[str] = None):
    """Log an interaction in user_audit_logs and refresh buyer intent score."""
    if not user_id:
        return
    try:
        with db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO user_audit_logs (user_id, tool_name, query_summary)
                VALUES (?, ?, ?)
                """,
                (user_id, tool_name, query_summary or "")
            )
            conn.commit()
        compute_buyer_intent(db, user_id)
    except Exception:
        pass
