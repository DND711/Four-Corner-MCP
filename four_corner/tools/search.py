"""
Property Search Tool for Four Corner MCP Server.
"""

from typing import Optional, List, Dict, Any
from four_corner.db.database import Database
from four_corner.models.schemas import UnitSearchResult


def search_verified_properties(
    db: Database,
    micro_market: Optional[str] = None,
    max_budget_cr: Optional[float] = None,
    min_budget_cr: Optional[float] = None,
    bhk: Optional[float] = None,
    facing: Optional[str] = None,
    corner_only: bool = False,
    morning_sunlight_only: bool = False,
    ready_by_year: Optional[int] = None,
    min_carpet_sqft: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Search verified residential developer inventory in Hyderabad with strict criteria.
    Guarantees direct developer pricing, true architectural carpet areas, and zero broker markups.
    """
    raw_results = db.search_properties(
        micro_market=micro_market,
        max_budget_cr=max_budget_cr,
        min_budget_cr=min_budget_cr,
        bhk=bhk,
        facing=facing,
        corner_only=corner_only,
        morning_sunlight_only=morning_sunlight_only,
        ready_by_year=ready_by_year,
        min_carpet_sqft=min_carpet_sqft,
    )

    results = []
    for r in raw_results:
        results.append(
            UnitSearchResult(
                unit_id=r["unit_id"],
                project_name=r["project_name"],
                developer=r["developer"],
                micro_market=r["micro_market"],
                bhk=r["bhk"],
                facing=r["facing"],
                is_corner_unit=bool(r["is_corner_unit"]),
                carpet_area_sqft=r["carpet_area_sqft"],
                super_built_up_sqft=r["super_built_up_sqft"],
                usable_efficiency_pct=r["usable_efficiency_pct"],
                total_price_cr=r["total_price_cr"],
                handover_date=r["handover_date"],
                rera_id=r["rera_id"],
            ).model_dump()
        )

    filters_applied = {
        "micro_market": micro_market or "All West Hyderabad",
        "budget_range_cr": f"₹{min_budget_cr or 0} Cr - ₹{max_budget_cr or 'Unlimited'} Cr",
        "bhk": bhk or "Any",
        "facing": facing or "Any",
        "corner_only": corner_only,
        "morning_sunlight_only": morning_sunlight_only,
        "ready_by_year": ready_by_year or "Any",
    }

    return {
        "status": "success",
        "matched_count": len(results),
        "filters_applied": filters_applied,
        "properties": results,
        "guarantee": "All listings pulled directly from official builder ERP records · Zero broker markups",
    }
