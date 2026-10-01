"""
Commute & Rush-Hour Traffic Analysis Tool for Four Corner MCP Server.
"""

from typing import Dict, Any, Optional
from four_corner.db.database import Database
from four_corner.models.schemas import CommuteEstimate


def calculate_rush_hour_commute(
    db: Database,
    project_id_or_name: str,
    destination_hub: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate realistic morning and evening rush-hour commute drive times from a residential development
    to Hyderabad's primary tech and commercial hubs (Financial District, HITEC City, Kokapet SEZ, Airport).
    Uses live congested commute benchmarks, not optimistic midnight estimates.
    """
    commute_records = db.get_commute_times(project_id_or_name, destination_hub)
    if not commute_records:
        return {
            "status": "error",
            "message": f"No commute routes found for project '{project_id_or_name}'.",
        }

    estimates = []
    for c in commute_records:
        estimates.append(
            CommuteEstimate(
                origin_project=c["project_name"],
                origin_micro_market=c["micro_market"],
                destination_hub=c["destination_hub"],
                distance_km=c["distance_km"],
                non_peak_mins=c["non_peak_mins"],
                rush_hour_morning_mins=c["rush_hour_morning_mins"],
                rush_hour_evening_mins=c["rush_hour_evening_mins"],
                primary_corridor=c["primary_corridor"],
                key_intersections=c["key_intersections"] if isinstance(c["key_intersections"], list) else [],
                congestion_warning=c.get("congestion_warning"),
            ).model_dump()
        )

    return {
        "status": "success",
        "project": commute_records[0]["project_name"],
        "micro_market": commute_records[0]["micro_market"],
        "commute_benchmarks": estimates,
        "commute_intelligence": "Drive times reflect 9:00 - 10:30 AM and 6:30 - 8:30 PM peak office traffic.",
    }
