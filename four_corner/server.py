import os
import sys
import argparse
import logging
from typing import Optional, List, Dict, Any
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from mcp.server.mcpserver import MCPServer

# Configure Unbuffered Logging for Real-Time Render Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger("four_corner")
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, "reconfigure") else None

from four_corner.config import SERVER_NAME
from four_corner.db.database import Database
from four_corner.openapi import get_openapi_spec
from four_corner.tools.search import search_verified_properties
from four_corner.tools.floor_plans import get_architectural_floor_plan
from four_corner.tools.pricing import get_transparent_pricing_breakdown, compare_properties
from four_corner.tools.commute import calculate_rush_hour_commute
from four_corner.tools.rera import verify_rera_filing
from four_corner.auth import (
    get_or_create_user,
    create_authorization_code,
    exchange_code_for_token,
    validate_access_token,
    save_user_favorite,
    submit_developer_inquiry,
    render_login_page,
)

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


@server.tool()
def save_favorite_unit(unit_id: str, buyer_email: str, notes: Optional[str] = None) -> Dict[str, Any]:
    """Save a residential unit to a buyer's personalized Four Corner portfolio.

    Args:
        unit_id: Unit identifier (e.g. 'AKR-T3-1202')
        buyer_email: Buyer email address
        notes: Optional custom notes
    """
    user = get_or_create_user(db=db, email=buyer_email, name=buyer_email.split("@")[0])
    return save_user_favorite(db=db, user_id=user["id"], unit_id=unit_id, notes=notes)


@server.tool()
def request_developer_callback(
    project_name: str,
    buyer_name: str,
    buyer_phone: str,
    buyer_email: str,
    unit_id: Optional[str] = None,
    preferred_time: Optional[str] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """Request a direct developer site visit or call with zero broker commission.
    Captures verified buyer contact details and schedules developer coordination.

    Args:
        project_name: Target development (e.g. 'My Home Akrida', 'Rajapushpa Provincia')
        buyer_name: Full name of the home buyer
        buyer_phone: WhatsApp contact phone number
        buyer_email: Buyer email address
        unit_id: Specific unit ID if applicable
        preferred_time: Preferred callback or site visit window (e.g. 'Saturday morning')
        notes: Specific buyer requirements
    """
    user = get_or_create_user(db=db, email=buyer_email, name=buyer_name, phone=buyer_phone)
    msg = f"Preferred Time: {preferred_time or 'Anytime'}. Notes: {notes or 'Direct developer inquiry'}"
    return submit_developer_inquiry(
        db=db,
        user_id=user["id"],
        project_name=project_name,
        inquiry_type="site_visit_request",
        unit_id=unit_id,
        user_message=msg
    )


@server.tool()
def get_user_portfolio(buyer_email: str) -> Dict[str, Any]:
    """Retrieve all saved units and inquiries in a buyer's Four Corner portfolio.

    Args:
        buyer_email: Buyer email address
    """
    user = get_or_create_user(db=db, email=buyer_email, name=buyer_email.split("@")[0])
    saved = db.get_user_portfolio(user_id=user["id"])
    inquiries = db.get_user_inquiries(user_id=user["id"])
    return {
        "status": "success",
        "buyer": {
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"],
            "preferred_market": user["micro_market_pref"]
        },
        "saved_units_count": len(saved),
        "saved_units": saved,
        "inquiries": inquiries
    }


# ==========================================
# OAuth 2.0 Server Endpoints (for ChatGPT & AI Authentication)
# ==========================================

@server.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])
@server.custom_route("/.well-known/openid-configuration", methods=["GET"])
async def oauth_discovery(request: Request) -> JSONResponse:
    """RFC 8414 & OpenID Connect discovery metadata.
    Enables ChatGPT to automatically configure Authorization, Token, and PKCE parameters."""
    base_url = str(request.base_url).rstrip("/")
    return JSONResponse({
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "userinfo_endpoint": f"{base_url}/oauth/userinfo",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic", "none"],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": ["openid", "profile", "email", "real_estate:read", "real_estate:write"],
        "service_documentation": f"{base_url}/"
    })


@server.custom_route("/oauth/authorize", methods=["GET"])
async def oauth_authorize_get(request: Request):
    """Serve the branded Four Corner login and buyer registration page with PKCE support."""
    from starlette.responses import HTMLResponse
    qp = request.query_params
    client_id = qp.get("client_id", "chatgpt-connector")
    redirect_uri = qp.get("redirect_uri", "")
    state = qp.get("state", "")
    code_challenge = qp.get("code_challenge", "")
    code_challenge_method = qp.get("code_challenge_method", "S256")

    html = render_login_page(
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method
    )
    return HTMLResponse(html)


@server.custom_route("/oauth/authorize", methods=["POST"])
async def oauth_authorize_post(request: Request):
    """Process buyer registration, create user record, and redirect with auth code."""
    from starlette.responses import RedirectResponse
    form = await request.form()

    name = str(form.get("name", "")).strip()
    email = str(form.get("email", "")).strip()
    phone = str(form.get("phone", "")).strip()

    
    client_id = str(form.get("client_id", "chatgpt-connector"))
    redirect_uri = str(form.get("redirect_uri", ""))
    state = str(form.get("state", ""))
    code_challenge = str(form.get("code_challenge", "")).strip() or None
    code_challenge_method = str(form.get("code_challenge_method", "S256")).strip() or None

    if not name:
        return JSONResponse({"error": "name_required", "message": "Full name is required"}, status_code=400)
    if not email:
        return JSONResponse({"error": "email_required", "message": "Email address is required"}, status_code=400)
    if not phone:
        return JSONResponse({"error": "phone_required", "message": "Phone number is required"}, status_code=400)

    logger.info(f"✅ Buyer Registered: {name} | Email: {email} | Phone: {phone}")

    # Save user into database
    user = get_or_create_user(
        db=db,
        email=email,
        name=name,
        phone=phone
    )


    # Create authorization code with PKCE challenge
    code = create_authorization_code(
        db=db,
        client_id=client_id,
        user_id=user["id"],
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method
    )

    # Redirect back to ChatGPT using HTTP 303 (See Other) so browsers perform a clean GET request
    delimiter = "&" if "?" in redirect_uri else "?"
    redirect_target = f"{redirect_uri}{delimiter}code={code}"
    if state:
        redirect_target += f"&state={state}"

    return RedirectResponse(url=redirect_target, status_code=303)


@server.custom_route("/oauth/token", methods=["POST"])
async def oauth_token(request: Request) -> JSONResponse:
    """OAuth 2.0 token endpoint: exchange authorization code for access token with PKCE verification."""
    code = None
    client_id = None
    client_secret = None
    code_verifier = None

    # Check for HTTP Basic Auth header (RFC 6749 Section 2.3.1)
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("basic "):
        try:
            import base64
            decoded = base64.b64decode(auth_header[6:].strip()).decode("utf-8")
            if ":" in decoded:
                client_id, client_secret = decoded.split(":", 1)
        except Exception:
            pass

    # Try parsing form data or json
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            code = body.get("code")
            client_id = client_id or body.get("client_id")
            client_secret = client_secret or body.get("client_secret")
            code_verifier = body.get("code_verifier")
        except Exception:
            pass
    else:
        form = await request.form()
        code = form.get("code")
        client_id = client_id or form.get("client_id")
        client_secret = client_secret or form.get("client_secret")
        code_verifier = form.get("code_verifier")

    if not code:
        return JSONResponse({"error": "invalid_request", "error_description": "Missing code parameter"}, status_code=400)

    token_payload, err = exchange_code_for_token(
        db=db,
        code=str(code),
        client_id=str(client_id) if client_id else None,
        client_secret=str(client_secret) if client_secret else None,
        code_verifier=str(code_verifier) if code_verifier else None
    )

    if err or not token_payload:
        return JSONResponse({"error": "invalid_grant", "error_description": err or "Failed to exchange code"}, status_code=400)

    return JSONResponse(token_payload)




@server.custom_route("/oauth/userinfo", methods=["GET"])
async def oauth_userinfo(request: Request) -> JSONResponse:
    """Return profile data of the currently authenticated buyer."""
    auth_header = request.headers.get("authorization", "")
    user = validate_access_token(db=db, token=auth_header)
    if not user:
        return JSONResponse({"error": "unauthorized", "message": "Invalid or expired access token"}, status_code=401)
    
    return JSONResponse({
        "sub": user["id"],
        "name": user["name"],
        "email": user["email"],
        "phone": user["phone"],
        "micro_market_pref": user["micro_market_pref"],
        "budget_max_cr": user["budget_max_cr"]
    })


@server.custom_route("/api/v1/admin/buyers", methods=["GET"])
async def admin_buyers(request: Request) -> JSONResponse:
    """Inspect all registered buyer leads and inquiries captured via ChatGPT & OAuth."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        buyers = [dict(r) for r in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM user_inquiries ORDER BY created_at DESC")
        inquiries = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM user_saved_units ORDER BY saved_at DESC")
        saved = [dict(r) for r in cursor.fetchall()]

    return JSONResponse({
        "total_buyers": len(buyers),
        "buyers": buyers,
        "total_inquiries": len(inquiries),
        "inquiries": inquiries,
        "total_saved_units": len(saved),
        "saved_units": saved
    })



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
# ASGI Application Factory with CORS & Transport Security
# ==========================================

from mcp.server.transport_security import TransportSecuritySettings

class ASGIRequestLogger:
    """Pure ASGI middleware to log incoming HTTP/SSE requests without BaseHTTPMiddleware streaming assertion errors."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            client = scope.get("client")
            client_ip = client[0] if client else "unknown"
            method = scope.get("method", "HTTP")
            path = scope.get("path", "")
            query = scope.get("query_string", b"").decode("utf-8", errors="ignore")
            target = f"{path}?{query}" if query else path

            logger.info(f"👉 [{client_ip}] {method} {target}")

            async def logging_send(message):
                if message["type"] == "http.response.start":
                    status = message.get("status", 200)
                    logger.info(f"👈 [{client_ip}] {method} {path} -> HTTP {status}")
                await send(message)

            await self.app(scope, receive, logging_send)
        else:
            await self.app(scope, receive, send)

def get_app():
    """Build and configure the Starlette ASGI application with CORS, logging, and remote transport security enabled."""
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
        allowed_hosts=["*"],
        allowed_origins=["*"]
    )
    asgi_app = server.sse_app(transport_security=security)
    asgi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return ASGIRequestLogger(asgi_app)


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
        logger.info(f"🚀 Four Corner Cloud Server listening on http://{args.host}:{args.port}")
        logger.info(f"   • Claude / ChatGPT MCP SSE: http://{args.host}:{args.port}/sse")
        logger.info(f"   • ChatGPT OpenAPI Schema:   http://{args.host}:{args.port}/openapi.json")
        logger.info(f"   • OAuth 2.0 Authorize URL: http://{args.host}:{args.port}/oauth/authorize")
        logger.info(f"   • Health Check Endpoint:    http://{args.host}:{args.port}/health")
        uvicorn.run("four_corner.server:app", host=args.host, port=args.port, log_level="info", access_log=True)
    else:
        # Standard local MCP stdio mode
        server.run(transport="stdio")


if __name__ == "__main__":
    main()


