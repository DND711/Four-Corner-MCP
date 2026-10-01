import os
import sys
import argparse
from typing import Optional, List, Dict, Any
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from mcp.server.mcpserver import MCPServer

from four_corner.config import SERVER_NAME
from four_corner.db.database import Database
from four_corner.openapi import get_openapi_spec
from four_corner.tools.search import search_verified_properties
from four_corner.tools.floor_plans import get_architectural_floor_plan
from four_corner.tools.pricing import get_transparent_pricing_breakdown, compare_properties
from four_corner.tools.commute import calculate_rush_hour_commute
from four_corner.tools.rera import verify_rera_filing

# Initialize MCP Server & Database
server = MCPServer(SERVER_NAME)
db = Database()


# ==========================================
# MCP Protocol Tools (for Claude & MCP Clients)
# ==========================================

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


# ==========================================
# REST API Endpoints (for ChatGPT Actions & Custom GPTs)
# ==========================================

@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Service health check."""
    return JSONResponse({
        "status": "healthy",
        "service": SERVER_NAME,
        "version": "1.0.0",
        "mcp_sse_endpoint": "/sse",
        "openapi_schema": "/openapi.json"
    })


@server.custom_route("/", methods=["GET"])
async def root_info(request: Request) -> JSONResponse:
    """Root metadata providing discovery URLs for ChatGPT and Claude."""
    base_url = str(request.base_url).rstrip("/")
    return JSONResponse({
        "title": "Four Corner Property Intelligence",
        "description": "Zero-Broker Real Estate Intelligence for Hyderabad",
        "mcp_sse_url": f"{base_url}/sse",
        "chatgpt_openapi_url": f"{base_url}/openapi.json",
        "endpoints": {
            "search": f"{base_url}/api/v1/properties/search",
            "floor_plan": f"{base_url}/api/v1/properties/floor-plan/{{unit_id}}",
            "pricing": f"{base_url}/api/v1/properties/pricing/{{unit_id}}",
            "compare": f"{base_url}/api/v1/properties/compare?unit_ids=AKR-T3-1202,PRV-T7-1403",
            "commute": f"{base_url}/api/v1/commute/calculate?project_name=My+Home+Akrida",
            "rera": f"{base_url}/api/v1/rera/verify?query=P02400005128"
        }
    })


@server.custom_route("/openapi.json", methods=["GET"])
async def openapi_schema(request: Request) -> JSONResponse:
    """Serve OpenAPI 3.1.0 schema for ChatGPT Custom GPT Actions."""
    base_url = str(request.base_url).rstrip("/")
    spec = get_openapi_spec(server_url=base_url)
    return JSONResponse(spec)


@server.custom_route("/api/v1/properties/search", methods=["GET"])
async def api_search(request: Request) -> JSONResponse:
    """REST endpoint for ChatGPT: Search properties."""
    qp = request.query_params
    
    max_budget_cr = float(qp["max_budget_cr"]) if "max_budget_cr" in qp else None
    min_budget_cr = float(qp["min_budget_cr"]) if "min_budget_cr" in qp else None
    bhk = float(qp["bhk"]) if "bhk" in qp else None
    ready_by_year = int(qp["ready_by_year"]) if "ready_by_year" in qp else None
    min_carpet_sqft = int(qp["min_carpet_sqft"]) if "min_carpet_sqft" in qp else None
    corner_only = qp.get("corner_only", "").lower() in ("true", "1", "yes")
    morning_sunlight_only = qp.get("morning_sunlight_only", "").lower() in ("true", "1", "yes")

    result = search_verified_properties(
        db=db,
        micro_market=qp.get("micro_market"),
        max_budget_cr=max_budget_cr,
        min_budget_cr=min_budget_cr,
        bhk=bhk,
        facing=qp.get("facing"),
        corner_only=corner_only,
        morning_sunlight_only=morning_sunlight_only,
        ready_by_year=ready_by_year,
        min_carpet_sqft=min_carpet_sqft,
    )
    return JSONResponse(result)


@server.custom_route("/api/v1/properties/floor-plan/{unit_id}", methods=["GET"])
async def api_floor_plan(request: Request) -> JSONResponse:
    """REST endpoint for ChatGPT: Architectural floor plan."""
    unit_id = request.path_params.get("unit_id", "")
    result = get_architectural_floor_plan(db=db, unit_id=unit_id)
    return JSONResponse(result)


@server.custom_route("/api/v1/properties/pricing/{unit_id}", methods=["GET"])
async def api_pricing(request: Request) -> JSONResponse:
    """REST endpoint for ChatGPT: Developer cost sheet."""
    unit_id = request.path_params.get("unit_id", "")
    result = get_transparent_pricing_breakdown(db=db, unit_id=unit_id)
    return JSONResponse(result)


@server.custom_route("/api/v1/properties/compare", methods=["GET"])
async def api_compare(request: Request) -> JSONResponse:
    """REST endpoint for ChatGPT: Compare multiple units."""
    raw_units = request.query_params.get("unit_ids", "")
    unit_ids = [u.strip() for u in raw_units.split(",") if u.strip()]
    if not unit_ids:
        return JSONResponse({"status": "error", "message": "Please provide unit_ids as comma-separated values"}, status_code=400)
    result = compare_properties(db=db, unit_ids=unit_ids)
    return JSONResponse(result)


@server.custom_route("/api/v1/commute/calculate", methods=["GET"])
async def api_commute(request: Request) -> JSONResponse:
    """REST endpoint for ChatGPT: Rush-hour commute times."""
    project_name = request.query_params.get("project_name", "")
    destination_hub = request.query_params.get("destination_hub")
    if not project_name:
        return JSONResponse({"status": "error", "message": "Missing required 'project_name' parameter"}, status_code=400)
    result = calculate_rush_hour_commute(db=db, project_id_or_name=project_name, destination_hub=destination_hub)
    return JSONResponse(result)


@server.custom_route("/api/v1/rera/verify", methods=["GET"])
async def api_rera(request: Request) -> JSONResponse:
    """REST endpoint for ChatGPT: TS-RERA legal verification."""
    query = request.query_params.get("query", "")
    if not query:
        return JSONResponse({"status": "error", "message": "Missing required 'query' parameter"}, status_code=400)
    result = verify_rera_filing(db=db, project_name_or_rera_id=query)
    return JSONResponse(result)


# ==========================================
# ASGI Application Factory with CORS
# ==========================================

def get_app():
    """Build and configure the Starlette ASGI application with CORS enabled."""
    asgi_app = server.sse_app()
    asgi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return asgi_app


app = get_app()


# ==========================================
# CLI Entrypoint (stdio or SSE HTTP server)
# ==========================================

def main():
    """Run the Four Corner server.
    
    Defaults to stdio for local Claude Desktop / Cursor usage.
    Specify --sse or set PORT environment variable for cloud-hosted web server.
    """
    parser = argparse.ArgumentParser(description="Four Corner Real Estate MCP Server")
    parser.add_argument("--sse", action="store_true", help="Run SSE HTTP web server for remote cloud hosting")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")), help="Port to listen on (default: 8000 or $PORT)")
    args, _ = parser.parse_known_args()

    # If PORT is explicitly set in environment or --sse is passed, run HTTP server
    if args.sse or os.getenv("PORT"):
        import uvicorn
        print(f"🚀 Starting Four Corner Cloud Server on {args.host}:{args.port}")
        print(f"   - Claude MCP SSE Endpoint: http://{args.host}:{args.port}/sse")
        print(f"   - ChatGPT OpenAPI Spec:   http://{args.host}:{args.port}/openapi.json")
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        # Standard local MCP stdio mode
        server.run(transport="stdio")


if __name__ == "__main__":
    main()

