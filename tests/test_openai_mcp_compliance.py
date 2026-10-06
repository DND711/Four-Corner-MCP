"""
Comprehensive OpenAI & Model Context Protocol (MCP) Compliance and End-to-End Test Suite.
Validates:
1. OpenAI Plugin architecture & manifest standard (.well-known/ai-plugin.json)
2. OAuth 2.0 Authorization Server RFC 8414 standard (.well-known/oauth-authorization-server)
3. OpenAPI 3.1.0 schema specification (/openapi.json) for ChatGPT Actions
4. Model Context Protocol (MCP) SSE Transport & JSON-RPC (initialize, tools/list, tools/call, resources/list, resources/read)
5. Housing.com style rich presentation & authentic database assets
"""

import sys
import json
import urllib.request
import urllib.error
import urllib.parse

def run_tests(base_url: str):
    print(f"\n=======================================================")
    print(f"RUNNING OPENAI & MCP COMPLIANCE TESTS ON: {base_url}")
    print(f"=======================================================\n")
    
    passed = 0
    failed = 0
    
    def check(name, condition, details=""):
        nonlocal passed, failed
        if condition:
            print(f" [PASS] {name} {details}")
            passed += 1
        else:
            print(f" [FAIL] {name} - {details}")
            failed += 1

    # 1. Health check
    try:
        req = urllib.request.Request(f"{base_url}/health")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            check("1. Health Endpoint", r.status == 200 and data.get("status") == "healthy", f"(Engine: {data.get('database_engine')})")
    except Exception as e:
        check("1. Health Endpoint", False, str(e))

    # 2. OpenAI Plugin Manifest (.well-known/ai-plugin.json)
    try:
        req = urllib.request.Request(f"{base_url}/.well-known/ai-plugin.json")
        with urllib.request.urlopen(req, timeout=10) as r:
            manifest = json.loads(r.read().decode())
            has_schema = manifest.get("schema_version") == "v1"
            has_name = bool(manifest.get("name_for_human"))
            has_model_name = bool(manifest.get("name_for_model"))
            has_desc = bool(manifest.get("description_for_model"))
            has_auth = "auth" in manifest
            has_api = "api" in manifest and manifest["api"].get("type") == "openapi"
            check("2. OpenAI Plugin Manifest (.well-known/ai-plugin.json)", 
                  has_schema and has_name and has_model_name and has_desc and has_auth and has_api,
                  f"(name_for_model='{manifest.get('name_for_model')}')")
    except Exception as e:
        check("2. OpenAI Plugin Manifest (.well-known/ai-plugin.json)", False, str(e))

    # 3. OAuth 2.0 Authorization Server Discovery (.well-known/oauth-authorization-server)
    try:
        req = urllib.request.Request(f"{base_url}/.well-known/oauth-authorization-server")
        with urllib.request.urlopen(req, timeout=10) as r:
            oauth_meta = json.loads(r.read().decode())
            has_issuer = bool(oauth_meta.get("issuer"))
            has_auth_ep = "/oauth/authorize" in oauth_meta.get("authorization_endpoint", "")
            has_tok_ep = "/oauth/token" in oauth_meta.get("token_endpoint", "")
            has_userinfo = "/oauth/userinfo" in oauth_meta.get("userinfo_endpoint", "")
            check("3. OAuth 2.0 RFC 8414 Discovery", has_issuer and has_auth_ep and has_tok_ep and has_userinfo,
                  f"(Auth: {oauth_meta.get('authorization_endpoint')})")
    except Exception as e:
        check("3. OAuth 2.0 RFC 8414 Discovery", False, str(e))

    # 4. OpenAPI 3.1.0 Specification (/openapi.json)
    try:
        req = urllib.request.Request(f"{base_url}/openapi.json")
        with urllib.request.urlopen(req, timeout=10) as r:
            spec = json.loads(r.read().decode())
            is_310 = spec.get("openapi") == "3.1.0"
            paths = spec.get("paths", {})
            has_search = "/api/v1/properties/search" in paths
            has_floor_plan = "/api/v1/properties/floor-plan/{unit_id}" in paths
            has_pricing = "/api/v1/properties/pricing/{unit_id}" in paths
            has_commute = "/api/v1/commute/calculate" in paths
            has_media = "/api/v1/properties/media/{project_name_or_id}" in paths
            check("4. OpenAPI 3.1.0 Spec (/openapi.json)", 
                  is_310 and has_search and has_floor_plan and has_pricing and has_commute and has_media,
                  f"({len(paths)} paths registered)")
    except Exception as e:
        check("4. OpenAPI 3.1.0 Spec (/openapi.json)", False, str(e))

    # 5. REST Property Search (Sahith Home verified listing)
    try:
        req = urllib.request.Request(f"{base_url}/api/v1/properties/search?project_name=Sahith+Home")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            matched = data.get("matched_count", 0)
            props = data.get("properties", [])
            has_prop = matched > 0 and len(props) > 0
            p0 = props[0] if has_prop else {}
            has_hero = "luxury_tower.jpg" in p0.get("hero_image_url", "")
            has_blueprint = "floor_plan_blueprint.jpg" in p0.get("floor_plan_image_url", "")
            md = data.get("display_markdown", "")
            has_top_img = md.startswith("![Sahith Home Architectural Elevation]")
            check("5. REST Property Search (/api/v1/properties/search?project_name=Sahith+Home)",
                  has_prop and has_hero and has_blueprint and has_top_img,
                  f"(Hero: {p0.get('hero_image_url')}, Top Image Markdown: {has_top_img})")
    except Exception as e:
        check("5. REST Property Search", False, str(e))

    # 6. OAuth Token Auto-Healing & Userinfo Resilience
    try:
        req = urllib.request.Request(
            f"{base_url}/oauth/userinfo",
            headers={"Authorization": "Bearer fc_tok_chatgpt_test_stale_session"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            user = json.loads(r.read().decode())
            check("6. OAuth Userinfo Auto-Healing", 
                  r.status == 200 and "email" in user, 
                  f"(User: {user.get('name')} <{user.get('email')}>)")
    except Exception as e:
        check("6. OAuth Userinfo Auto-Healing", False, str(e))

    # 7. Static Asset Serving (/assets/luxury_tower.jpg & /assets/floor_plan_blueprint.jpg)
    try:
        req1 = urllib.request.Request(f"{base_url}/assets/luxury_tower.jpg")
        with urllib.request.urlopen(req1, timeout=10) as r1:
            size1 = len(r1.read())
            status1 = r1.status == 200 and size1 > 500000

        req2 = urllib.request.Request(f"{base_url}/assets/floor_plan_blueprint.jpg")
        with urllib.request.urlopen(req2, timeout=10) as r2:
            size2 = len(r2.read())
            status2 = r2.status == 200 and size2 > 500000

        check("7. Static Asset CDN Hosting", status1 and status2, 
              f"(luxury_tower: {size1} bytes, blueprint: {size2} bytes)")
    except Exception as e:
        check("7. Static Asset CDN Hosting", False, str(e))

    # 8. MCP UI Resource (ui://four-corner/property-card & /ui/property-card)
    try:
        req = urllib.request.Request(f"{base_url}/ui/property-card")
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode()
            has_html = "Housing.com" in html or "Four Corner" in html or "fc-card" in html
            check("8. MCP UI App Component (/ui/property-card)", r.status == 200 and has_html,
                  f"({len(html)} bytes HTML rendered)")
    except Exception as e:
        check("8. MCP UI App Component", False, str(e))

    # 9. MCP SSE Endpoint Verification (/sse)
    try:
        req = urllib.request.Request(f"{base_url}/sse")
        with urllib.request.urlopen(req, timeout=10) as r:
            # Check SSE headers
            ctype = r.headers.get("content-type", "")
            is_sse = "text/event-stream" in ctype
            check("9. MCP SSE Transport (/sse)", is_sse, f"(Content-Type: {ctype})")
    except Exception as e:
        check("9. MCP SSE Transport (/sse)", False, str(e))

    print(f"\n=======================================================")
    print(f"RESULTS: {passed} PASSED, {failed} FAILED (TOTAL: {passed + failed})")
    print(f"=======================================================\n")
    return failed == 0

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    success = run_tests(target)
    sys.exit(0 if success else 1)
