# Four Corner MCP — Architecture Gotchas & Evolution Roadmap

> **Document Version:** 1.0.0  
> **Last Updated:** October 2026  
> **System:** Four Corner Real Estate Intelligence Protocol (MCP + OpenAPI + OAuth 2.0)  
> **Repository:** [https://github.com/DND711/Four-Corner-MCP](https://github.com/DND711/Four-Corner-MCP)

---

## 1. Critical Technical Considerations & Hard-Learned Lessons

This section documents critical production failure modes, architectural nuances, and integration traps discovered while deploying Four Corner to Render and connecting it to ChatGPT and Claude.

### Consideration 1: Starlette's `BaseHTTPMiddleware` Breaks Streaming (SSE)
* **The Symptom:**
  ```text
  AssertionError: Unexpected message: {'type': 'http.response.start', 'status': 200, ...}
  File "starlette/middleware/base.py", line 183, in body_stream
    assert message["type"] == "http.response.body"
  ```
* **The Root Cause:**
  Starlette's `BaseHTTPMiddleware` wraps response bodies with an async generator (`body_stream`) expecting strict body chunks. When handling Server-Sent Events (`/sse`) or asynchronous MCP session channels (`/messages/`), ASGI `http.response.start` events can arrive concurrently or out of order. `BaseHTTPMiddleware` fails its internal assertion and crashes the ASGI application.
* **The Solution:**
  **Never use `BaseHTTPMiddleware` for streaming endpoints.** We replaced it with a pure ASGI middleware (`ASGIRequestLogger`) that intercepts raw ASGI `scope`, `receive`, and `send` callables without wrapping the body generator.

---

### Consideration 2: Ephemeral Filesystem on Docker / Render Deployments
* **The Symptom:**
  Running `curl https://<app>.onrender.com/api/v1/admin/buyers` returns `total_buyers: 0` immediately following a git push or container rebuild, even though users previously registered.
* **The Root Cause:**
  Default Docker web services on Render run on ephemeral container filesystems. When a new commit is deployed, Render spins up a fresh container instance. The SQLite database at `/root/.four-corner/four_corner.db` is initialized from scratch.
* **The Solution:**
  1. We made `init_database()` automatically re-seed property inventory and TS-RERA benchmarks on container startup while clearing duplicates.
  2. For user lead persistence across production deploys, the database path must either be mounted to a **Render Persistent Disk** or migrated to managed **PostgreSQL (Supabase / Neon / Render Postgres)**.

---

### Consideration 3: The "Discrepancy Trigger" in AI Models (Web Search Fallback)
* **The Symptom:**
  When asked a property or commute question, ChatGPT ignored the MCP tool, performed a public web search, found contradictory marketing blogs, and told the user: *"Four Corner's listing needs verification... RERA ID not found"*.
* **The Root Cause:**
  Modern AI agents (like GPT-4o with web browsing) cross-check tool outputs against their training data or search index. If a placeholder RERA ID or slightly mismatched micro-market name is returned, the model loses confidence in the tool and warns the user.
* **The Solution:**
  1. **Strict TS-RERA Alignment:** Every RERA number must be the exact, registered Telangana State RERA ID (e.g., Candeur Lakescape is `P02400005724`, not an internal placeholder).
  2. **Smart Fallback Matching in Queries:** In `get_commute_times()`, querying `"ADP"` or `"my office"` automatically maps to `"Financial District / ADP Gachibowli"`.
  3. **Embedded Protocol Instructions:** Passing `instructions=SERVER_INSTRUCTIONS` into `MCPServer` directly instructs ChatGPT during the handshake to never doubt verified tool data.

---

### Consideration 4: Strict OAuth 2.0 PKCE S256 Enforcement by OpenAI
* **The Symptom:**
  ChatGPT connector failed registration with:
  `OAuth authorization server metadata must advertise PKCE support with code_challenge_methods_supported containing S256`.
* **The Root Cause:**
  OpenAI's connected apps mandate strict RFC 8414 metadata discovery. Even if code exchange works locally, ChatGPT verifies that `/.well-known/oauth-authorization-server` advertises `code_challenge_methods_supported: ["S256"]`.
* **The Solution:**
  We implemented full RFC 7636 PKCE validation with SHA-256 base64url verification in `four_corner/auth.py`, complete with `/.well-known/oauth-authorization-server` and `/oauth/userinfo` bearer token endpoints.

---

### Consideration 5: Reasoning Models Leaking Raw JSON in Chat Output
* **The Symptom:**
  ChatGPT printed a raw code block `{"unit_id": "CND-T5-1602"}` in plain text directly above the tool response widget.
* **The Root Cause:**
  When "Think" mode is active, the model sometimes echoes parameter arguments into the response buffer before triggering the execution step.
* **The Solution:**
  Added **Directive 6** to `SERVER_INSTRUCTIONS`:
  > *"NEVER output raw JSON, parameter payloads, or code blocks in your chat text. Execute all tool calls invisibly in the background, and present the final answer in clean, human-readable conversational formatting."*

---

### Consideration 6: Accordion Tool UI in ChatGPT
* **The Nuance:**
  Users often mistake the `{=} Received app response ^` widget for unformatted output.
* **The Reality:**
  This is ChatGPT's native tool inspection accordion. Older tool calls are collapsed (`3 earlier tool calls hidden`). Clicking the expanded header collapses it back into a single clean line.

---

## 2. Tested Milestones and Production Status (Real-World Milestones)

| Feature | Status | Description |
| :--- | :---: | :--- |
| **Dual-Protocol Server** | Active | Serves both Claude/Cursor MCP (`/sse`) and ChatGPT Actions (`/openapi.json`). |
| **Render Cloud Deployment** | Active | Dockerized Python 3.11 environment with live auto-deploy on git push. |
| **Real-Time Unbuffered Logging** | Active | `PYTHONUNBUFFERED=1` enables immediate log streaming to Render CLI/dashboard. |
| **OAuth 2.0 PKCE Auth Engine** | Active | Mandatory phone number validation, auth codes, and Bearer token issuance. |
| **Lead Capture Admin API** | Active | `GET /api/v1/admin/buyers` lets administrators monitor registered buyers & inquiries. |
| **Verified Inventory Under ₹1.2 Cr** | Active | Authentic 2, 2.5, and 3-BHK inventory across Financial District, Tellapur, Gachibowli, Nallagandla, Narsingi, and Kollur. |
| **ADP Gachibowli Commute Engine**| Active | Rush-hour morning (9:00–10:30 AM) & evening (6:30–8:30 PM) road transit benchmarks to ADP office in Nanakramguda. |
| **Architectural Floor Plan Math** | Active | Room-by-room carpet dimensions, true usable efficiency, and balcony sunlight metrics. |
| **Itemized Builder Cost Sheets** | Active | Base cost + floor rise + corner premium + parking + clubhouse + infra + GST calculation with ₹0 broker markup. |
| **Official TS-RERA Verification** | Active | Clean-chit verification, escrow compliance check, and litigation history audit. |
| **Automated Test Suite** | 11/11 Passed | Full unit & integration testing via `pytest -v`. |

---

## 3. Future Development Roadmap

### Phase 1: Database & Production Persistence (Immediate Next Step)
- [ ] **Migrate SQLite to Managed PostgreSQL:**
  - Connect Render to a persistent PostgreSQL instance (Render Postgres, Supabase, or Neon).
  - Ensures registered buyer accounts, saved portfolios, and inquiries survive container redeploys.
  - Implement Alembic database migrations.
- [ ] **Webhook Alerts for New Leads:**
  - Send instant Telegram/Slack/WhatsApp notifications to the admin when a new buyer registers or submits an inquiry.

### Phase 2: Live Data Ingestion & RERA Automation
- [ ] **Automated TS-RERA Scraper & Syncer:**
  - Scheduled background worker to poll `rera.telangana.gov.in` for quarterly construction progress reports, updated tower completion dates, and new project filings.
- [ ] **Live Traffic API Integration:**
  - Augment static rush-hour corridor models with live Google Maps Distance Matrix API / TomTom API calls (with Redis caching to minimize API costs).
  - Add real-time monsoon waterlogging alerts on low-lying Hyderabad tech corridors (e.g., Gachibowli junction, Bio-diversity underpass).

### Phase 3: Architectural & Visual Intelligence
- [ ] **Interactive Floor Plan Rendering:**
  - Return high-resolution architectural SVG/PNG floor plans via MCP media resources (`read_resource`).
  - Room layout visualizer highlighting load-bearing walls vs customizable partitions.
- [ ] **Balcony Sunlight Simulation:**
  - Sun path calculations based on unit orientation (azimuth/elevation) showing exact hours of direct morning sunlight across summer vs winter solstices.

### Phase 4: Buyer Transaction & Negotiation Tools
- [ ] **Direct Developer Booking Webhook:**
  - Secure integration with builder CRM systems (Sell.do, Salesforce, LeadSquared) to allow buyers to lock inventory directly without intermediary broker intervention.
- [ ] **Down Payment & Construction-Linked EMI Calculator:**
  - Detailed milestone-based payment schedules (e.g., 10% booking, 10% plinth, 10% slab-by-slab, 5% possession) with projected interest outgo during the construction period.
- [ ] **Bank Pre-Approval Checker:**
  - Check project pre-approval status with major lending institutions (SBI, HDFC, ICICI, Axis).

### Phase 5: Geographic Expansion
- [ ] **Phase 1 Expansion (Hyderabad East & North):**
  - Uppal, Pocharam, Kompally, Medchal.
- [ ] **Phase 2 Expansion (National IT Corridors):**
  - **Bengaluru:** Whitefield, Bellandur, Sarjapur, Outer Ring Road.
  - **Pune:** Hinjawadi, Kharadi, Wakad.
