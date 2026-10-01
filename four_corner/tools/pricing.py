"""
Transparent Developer Pricing Tool for Four Corner MCP Server.
"""

from typing import Dict, Any, List
from four_corner.db.database import Database
from four_corner.models.schemas import PriceBreakdown


def get_transparent_pricing_breakdown(db: Database, unit_id: str) -> Dict[str, Any]:
    """
    Generate an unadulterated builder cost sheet for a specific unit.
    Reveals all hidden components: base rate, floor rise, corner premium, parking, clubhouse, and GST.
    Guarantees 100% direct developer pricing with zero broker commission.
    """
    unit_data = db.get_unit_details(unit_id)
    if not unit_data:
        return {
            "status": "error",
            "message": f"Unit ID '{unit_id}' not found.",
        }

    sbu = unit_data["super_built_up_sqft"]
    carpet = unit_data["carpet_area_sqft"]
    base_rate = unit_data["base_rate_per_sqft"]
    base_cost = sbu * base_rate
    floor_rise = unit_data["floor_rise_charges"]
    corner_prem = unit_data["corner_premium_charges"]
    clubhouse = unit_data["clubhouse_charges"]
    car_parking = unit_data["car_parking_charges"]
    infra = unit_data["infra_charges"]

    subtotal = base_cost + floor_rise + corner_prem + clubhouse + car_parking + infra
    gst = int(subtotal * 0.05)
    total_out_the_door = subtotal + gst
    total_cr = round(total_out_the_door / 10000000.0, 2)
    true_cost_per_carpet = int(total_out_the_door / carpet)

    breakdown = PriceBreakdown(
        unit_id=unit_data["id"],
        project_name=unit_data["project_name"],
        developer=unit_data["developer"],
        super_built_up_sqft=sbu,
        carpet_area_sqft=carpet,
        base_rate_per_sqft_inr=base_rate,
        base_cost_inr=base_cost,
        floor_rise_charges_inr=floor_rise,
        corner_premium_charges_inr=corner_prem,
        clubhouse_charges_inr=clubhouse,
        car_parking_slots=unit_data["car_parking_slots"],
        car_parking_charges_inr=car_parking,
        infrastructure_and_water_inr=infra,
        gst_inr=gst,
        total_out_the_door_inr=total_out_the_door,
        total_in_crores=total_cr,
        true_cost_per_carpet_sqft_inr=true_cost_per_carpet,
        broker_commission_inr=0,
    )

    return {
        "status": "success",
        "pricing_breakdown": breakdown.model_dump(),
        "transparency_audit": {
            "quoted_builder_rate": f"₹{base_rate:,} / sqft (SBU basis)",
            "effective_carpet_rate": f"₹{true_cost_per_carpet:,} / sqft (True usable carpet basis)",
            "broker_markup_savings": "₹0 broker commission included. Standard brokers charge 1-2% (₹1.5L - ₹3.5L saved).",
        }
    }


def compare_properties(db: Database, unit_ids: List[str]) -> Dict[str, Any]:
    """
    Compare multiple properties side-by-side on true usable carpet area, actual price-per-carpet-sqft,
    and developer delivery metrics.
    """
    comparison_table = []
    for uid in unit_ids:
        unit = db.get_unit_details(uid)
        if not unit:
            continue
        
        carpet = unit["carpet_area_sqft"]
        total_inr = unit["total_out_the_door_inr"]
        true_carpet_rate = int(total_inr / carpet)

        comparison_table.append({
            "unit_id": unit["id"],
            "project": unit["project_name"],
            "developer": unit["developer"],
            "micro_market": unit["micro_market"],
            "bhk": unit["bhk"],
            "facing": unit["facing"],
            "super_built_up_sqft": unit["super_built_up_sqft"],
            "carpet_area_sqft": carpet,
            "usable_efficiency": f"{unit['usable_efficiency_pct']}%",
            "all_inclusive_price_cr": f"₹{unit['total_price_cr']} Cr",
            "true_rate_per_carpet_sqft": f"₹{true_carpet_rate:,}",
            "handover": unit["registered_handover_date"],
        })

    return {
        "status": "success",
        "units_compared_count": len(comparison_table),
        "comparison": comparison_table,
    }
