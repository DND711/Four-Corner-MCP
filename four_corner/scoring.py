"""
Four Corner Buyer Readiness Scoring System.
Calculates purchase readiness and buyer score using a weighted activity model
with recency decay, casual browsing filtering, and direct developer inquiries.
"""

import json
import math
from typing import Dict, Any, Optional
from datetime import datetime, timezone


def compute_buyer_intent(db, user_id: str) -> Dict[str, Any]:
    """
    Calculates a purchase readiness score (0% - 100%) for a buyer.
    
    Evaluation workflow:
      1. Activity Recency:
         Weights recent actions higher using a 14-day half-life.
      2. Casual Browsing Filter:
         Floor plan views without price checks or inquiry activity receive lower weight.
      3. Activity Weighting:
         Evaluates budget clarity, commute checks, unit reviews, legal checks, and developer inquiries.
      4. Score Calibration:
         Combines weighted dimensions into a 0 to 100 readiness score.
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

        # 3. Fetch direct developer inquiries
        cursor.execute("SELECT * FROM user_inquiries WHERE user_id = ?", (user_id,))
        inquiries = [dict(r) for r in cursor.fetchall()]
        inquiry_count = len(inquiries)

        # 4. Fetch activity logs
        cursor.execute("SELECT * FROM user_audit_logs WHERE user_id = ?", (user_id,))
        audit_logs = [dict(l) for l in cursor.fetchall()]

        # 5. Fetch search events
        cursor.execute("SELECT * FROM search_events WHERE user_id = ?", (user_id,))
        search_events = [dict(s) for s in cursor.fetchall()]

    # Cold visitor with no signals has 0 score
    total_signals = len(audit_logs) + saved_count + inquiry_count + len(search_events)
    has_profile_signal = bool(user.get("phone") or user.get("budget_max_cr") or user.get("bhk_pref"))

    if total_signals == 0 and not has_profile_signal:
        empty_breakdown = {
            "financial_precision": {"score": 0, "max": 25, "pct": 0.0},
            "commute_alignment": {"score": 0, "max": 20, "pct": 0.0},
            "architectural_depth": {"score": 0, "max": 20, "pct": 0.0},
            "legal_due_diligence": {"score": 0, "max": 15, "pct": 0.0},
            "commitment_signals": {"score": 0, "max": 20, "pct": 0.0},
        }
        return {
            "user_id": user_id,
            "intent_score": 0,
            "buyer_tier": "CASUAL_BROWSER",
            "readiness_label": "Casual Browser (Browsing properties)",
            "recommended_action": "Provide standard property search results",
            "breakdown": empty_breakdown,
            "total_saved_units": 0,
            "total_inquiries": 0,
            "total_audit_events": 0,
            "total_searches": 0,
            "probability_math": {
                "model": "Buyer Readiness Model",
                "probability_pct": 0.0,
                "score": 0,
                "half_life_days": 14.0,
                "casual_filter_active": True
            }
        }

    # ----------------------------------------------------
    # 1. Activity Recency Weighting (14-day half-life)
    # ----------------------------------------------------
    HALF_LIFE_DAYS = 14.0
    now = datetime.now(timezone.utc)

    def get_decay_weight(created_at_val) -> float:
        if not created_at_val:
            return 1.0
        try:
            ts_str = str(created_at_val).replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delta_days = (now - dt).total_seconds() / 86400.0
            return math.exp(-0.693147 * max(0.0, delta_days) / HALF_LIFE_DAYS)
        except Exception:
            return 1.0

    # Aggregate recency-weighted activity counts
    tool_weights: Dict[str, float] = {}
    for log in audit_logs:
        t_name = log.get("tool_name", "")
        w = get_decay_weight(log.get("created_at"))
        tool_weights[t_name] = tool_weights.get(t_name, 0.0) + w

    pricing_w = tool_weights.get("get_pricing_breakdown", 0.0)
    rera_w = tool_weights.get("verify_rera_status", 0.0)
    commute_w = tool_weights.get("calculate_commute", 0.0)
    fp_w = tool_weights.get("get_floor_plan", 0.0)

    # ----------------------------------------------------
    # 2. Casual Browsing Filter
    # ----------------------------------------------------
    # Viewing luxury or high floors casually without price checks or inquiries
    # is weighted lower unless supported by practical pricing or commute checks.
    practical_checks = pricing_w + rera_w + commute_w
    casual_discount = min(1.0, 0.25 + 0.75 * min(1.0, practical_checks / 1.5))

    # ----------------------------------------------------
    # 3. Activity Scores for 5 Key Areas
    # ----------------------------------------------------

    # Area 1: Budget & Price Verification
    lam_fin = 0.0
    if user.get("budget_max_cr") and float(user["budget_max_cr"]) > 0:
        lam_fin += 0.40
    lam_fin += 0.50 * pricing_w
    lam_fin += 0.35 * tool_weights.get("compare_units", 0.0)
    searches_with_budget = sum(1 for s in search_events if s.get("max_budget_cr"))
    if searches_with_budget > 0:
        lam_fin += 0.20 * math.log(1.0 + searches_with_budget)
    s_fin = 1.0 - math.exp(-lam_fin)

    # Area 2: Commute & Location Check
    lam_comm = 0.55 * commute_w
    has_workplace_query = any(
        "adp" in str(l.get("query_summary", "")).lower() or 
        "hitec" in str(l.get("query_summary", "")).lower() or
        "financial district" in str(l.get("query_summary", "")).lower() or
        "gachibowli" in str(l.get("query_summary", "")).lower()
        for l in audit_logs
    )
    if has_workplace_query:
        lam_comm += 0.45
    s_comm = 1.0 - math.exp(-lam_comm)

    # Area 3: Unit & Floor Plan Review
    lam_arch = 0.50 * fp_w * casual_discount
    if user.get("bhk_pref"):
        lam_arch += 0.30
    has_arch_filter = any(
        "sunlight" in str(l.get("query_summary", "")).lower() or 
        "corner" in str(l.get("query_summary", "")).lower()
        for l in audit_logs
    ) or any(s.get("corner_only") or s.get("morning_sunlight_only") for s in search_events)
    if has_arch_filter:
        lam_arch += 0.40
    s_arch = 1.0 - math.exp(-lam_arch)

    # Area 4: TS-RERA & Sanction Verification
    lam_leg = 0.65 * rera_w
    has_legal_check = any("rera" in str(l.get("query_summary", "")).lower() or "sanction" in str(l.get("query_summary", "")).lower() for l in audit_logs)
    if has_legal_check:
        lam_leg += 0.40
    s_leg = 1.0 - math.exp(-lam_leg)

    # Area 5: Saved Units & Direct Developer Inquiries
    lam_act = 0.0
    if user.get("phone"):
        lam_act += 0.35
    lam_act += 0.50 * saved_count + 0.80 * inquiry_count
    s_act = 1.0 - math.exp(-lam_act)

    # ----------------------------------------------------
    # 4. Overall Score Calculation
    # ----------------------------------------------------
    BETA_0  = -2.2
    W_FIN   = 1.6
    W_COMM  = 1.3
    W_ARCH  = 1.3
    W_LEG   = 1.0
    W_ACT   = 1.8

    z_total = BETA_0 + (
        W_FIN  * s_fin +
        W_COMM * s_comm +
        W_ARCH * s_arch +
        W_LEG  * s_leg +
        W_ACT  * s_act
    )

    probability_pct = 100.0 / (1.0 + math.exp(-z_total))
    total_score = int(round(probability_pct))

    # ----------------------------------------------------
    # 5. Readiness Tiers & Recommendations
    # ----------------------------------------------------
    if total_score >= 75:
        tier = "TRANSACTION_READY"
        readiness_label = "Ready to Buy (Active Developer Inquiries)"
        recommended_action = "Connect buyer directly with developer sales team for unit booking"
    elif total_score >= 50:
        tier = "SERIOUS_EVALUATOR"
        readiness_label = "Active Evaluator (Reviewing Prices & Plans)"
        recommended_action = "Provide full price breakdown and bank loan approval details"
    elif total_score >= 25:
        tier = "WARM_RESEARCHER"
        readiness_label = "Active Researcher (Comparing Projects & Locations)"
        recommended_action = "Share location comparisons and project handover schedules"
    else:
        tier = "CASUAL_BROWSER"
        readiness_label = "Casual Browser (Browsing properties)"
        recommended_action = "Provide standard property search results"

    breakdown = {
        "financial_precision": {
            "score": int(round(25 * s_fin)),
            "max": 25,
            "pct": round(s_fin * 100, 1)
        },
        "commute_alignment": {
            "score": int(round(20 * s_comm)),
            "max": 20,
            "pct": round(s_comm * 100, 1)
        },
        "architectural_depth": {
            "score": int(round(20 * s_arch)),
            "max": 20,
            "pct": round(s_arch * 100, 1)
        },
        "legal_due_diligence": {
            "score": int(round(15 * s_leg)),
            "max": 15,
            "pct": round(s_leg * 100, 1)
        },
        "commitment_signals": {
            "score": int(round(20 * s_act)),
            "max": 20,
            "pct": round(s_act * 100, 1)
        },
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
        "total_audit_events": len(audit_logs),
        "total_searches": len(search_events),
        "probability_math": {
            "model": "Buyer Readiness Model",
            "readiness_score": total_score,
            "half_life_days": HALF_LIFE_DAYS,
            "verified_inquiries": inquiry_count
        }
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
