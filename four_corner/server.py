"""
Four Corner MCP Server - Property Intelligence & Verified Real Estate for AI Assistants.
"""

from typing import Optional, List, Dict, Any
from mcp.server.mcpserver import MCPServer

from four_corner.config import SERVER_NAME
from four_corner.db.database import Database
from four_corner.tools.search import search_verified_properties
from four_corner.tools.floor_plans import get_architectural_floor_plan
from four_corner.tools.pricing import get_transparent_pricing_breakdown, compare_properties
from four_corner.tools.commute import calculate_rush_hour_commute
from four_corner.tools.rera import verify_rera_filing

# Initialize MCP Server & Database
server = MCPServer(SERVER_NAME)
db = Database()


@server.tool()
def search_properties(
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
    """Search verified residential developer inventory in Hyderabad with strict criteria.
    Guarantees direct developer pricing, true architectural carpet areas, and zero broker markups.

    Args:
        micro_market: Target neighborhood (Kokapet, Financial District, Tellapur, Narsingi, Gachibowli)
        max_budget_cr: Upper budget limit in Crores (e.g., 1.4 for ₹1.4 Cr)
        min_budget_cr: Lower budget limit in Crores
        bhk: Desired configuration (e.g., 2, 2.5, 3, 4, 4.5)
        facing: Unit orientation (East, West, North, South)
        corner_only: Filter for corner apartments with dual-aspect ventilation
        morning_sunlight_only: Require east/north-east facing balconies with direct morning sun
        ready_by_year: Maximum acceptable handover year (e.g., 2026)
        min_carpet_sqft: Minimum actual usable indoor carpet area in sq ft
    """
    return search_verified_properties(
        db=db,
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


@server.tool()
def get_floor_plan(unit_id: str) -> Dict[str, Any]:
    """Retrieve verified architectural blueprints and room-by-room carpet dimensions for a specific unit.
    Calculates exact usable efficiency without inflated builder super built-up math.

    Args:
        unit_id: Unique unit identifier (e.g., 'AKR-T3-1202', 'TRK-T2-1801')
    """
    return get_architectural_floor_plan(db=db, unit_id=unit_id)


@server.tool()
def get_pricing_breakdown(unit_id: str) -> Dict[str, Any]:
    """Generate an unadulterated builder cost sheet for a specific unit.
    Reveals all hidden components: base rate, floor rise, corner premium, parking, clubhouse, and GST.
    Guarantees 100% direct developer pricing with zero broker commission.

    Args:
        unit_id: Unique unit identifier (e.g., 'AKR-T3-1202', 'PRV-T7-1403')
    """
    return get_transparent_pricing_breakdown(db=db, unit_id=unit_id)


@server.tool()
def calculate_commute(
    project_id_or_name: str,
    destination_hub: Optional[str] = None
) -> Dict[str, Any]:
    """Calculate realistic morning and evening rush-hour commute drive times from a residential development
    to Hyderabad's primary tech and commercial hubs (Financial District, HITEC City, Kokapet SEZ, Airport).
    Uses congested peak-traffic benchmarks, not optimistic midnight estimates.

    Args:
        project_id_or_name: Project name or ID (e.g., 'My Home Akrida', 'Rajapushpa Provincia')
        destination_hub: Target employment hub ('Financial District', 'HITEC City', 'Kokapet SEZ', 'RGIA Airport')
    """
    return calculate_rush_hour_commute(
        db=db,
        project_id_or_name=project_id_or_name,
        destination_hub=destination_hub
    )


@server.tool()
def verify_rera(project_name_or_rera_id: str) -> Dict[str, Any]:
    """Verify official Telangana State Real Estate Regulatory Authority (TS-RERA) registration status,
    approved building sanctions, designated escrow bank accounts, and quarterly filing health of any project.

    Args:
        project_name_or_rera_id: TS-RERA ID (e.g., 'P02400005128') or project name
    """
    return verify_rera_filing(db=db, project_name_or_rera_id=project_name_or_rera_id)


@server.tool()
def compare_units(unit_ids: List[str]) -> Dict[str, Any]:
    """Compare multiple residential units side-by-side on true usable carpet area, actual price-per-carpet-sqft,
    and developer delivery metrics.

    Args:
        unit_ids: List of unit IDs to compare (e.g., ['AKR-T3-1202', 'PRV-T7-1403'])
    """
    return compare_properties(db=db, unit_ids=unit_ids)


def main():
    """Run the Four Corner MCP server via standard stdio transport."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
