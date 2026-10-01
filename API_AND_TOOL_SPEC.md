# Four Corner — API & Tool Specification Reference

> **Server Name:** `four-corner`  
> **Protocol Support:** Model Context Protocol (MCP 2024-11-05 via SSE) + OpenAPI 3.1.0 (REST)  
> **Production Base URL:** `https://four-corner-mcp.onrender.com`

---

## 🛠️ 1. MCP Tools Reference (Claude, Cursor & ChatGPT Plugins)

When an AI client connects via SSE (`/sse`), the following 7 tools are registered:

### 1. `search_properties`
* **Description:** Search verified direct-developer residential inventory in Hyderabad with strict filtering criteria.
* **Arguments:**
  | Argument | Type | Required | Description |
  | :--- | :--- | :---: | :--- |
  | `micro_market` | `string` | No | Target neighborhood (`Kokapet`, `Financial District`, `Tellapur`, `Narsingi`, `Gachibowli`, `Kollur`, `Nallagandla`) |
  | `max_budget_cr` | `number` | No | Maximum total budget ceiling in Crores (e.g. `1.2` for ₹1.2 Cr) |
  | `min_budget_cr` | `number` | No | Minimum budget in Crores |
  | `bhk` | `number` | No | Target configuration (`2`, `2.5`, `3`, `4`) |
  | `facing` | `string` | No | Unit orientation (`East`, `West`, `North`, `South`) |
  | `corner_only` | `boolean` | No | Filter for dual-aspect corner units with cross-ventilation |
  | `morning_sunlight_only` | `boolean` | No | Filter for East/North-East facing balconies with morning sunlight |
  | `ready_by_year` | `integer` | No | Maximum acceptable handover year (e.g. `2026`) |
  | `min_carpet_sqft` | `integer` | No | Minimum usable indoor carpet area in sq ft |
* **Example Return:**
  ```json
  {
    "status": "success",
    "matched_count": 1,
    "filters_applied": {
      "micro_market": "Financial District",
      "budget_range_cr": "₹0.6 Cr - ₹1.2 Cr"
    },
    "properties": [
      {
        "unit_id": "ZEN-T9-0402",
        "project_name": "Aparna Zenon",
        "developer": "Aparna Constructions",
        "micro_market": "Financial District",
        "bhk": 2.0,
        "facing": "East",
        "is_corner_unit": false,
        "carpet_area_sqft": 885,
        "super_built_up_sqft": 1240,
        "usable_efficiency_pct": 71.4,
        "total_price_cr": 1.08,
        "handover_date": "2027-03-31",
        "rera_id": "P02400003719"
      }
    ]
  }
  ```

---

### 2. `calculate_commute`
* **Description:** Calculate realistic peak rush-hour commute metrics to primary tech corridors and corporate offices. Automatically maps "my location" or "my office" to **ADP Gachibowli (Nanakramguda)**.
* **Arguments:**
  | Argument | Type | Required | Description |
  | :--- | :--- | :---: | :--- |
  | `project_id_or_name` | `string` | Yes | Project name or ID (e.g., `Candeur Lakescape`, `Aparna Zenon`) |
  | `destination_hub` | `string` | No | Target hub (default: `ADP` or `Financial District`, also supports `HITEC City`, `Kokapet SEZ`, `RGIA Airport`) |
* **Example Return:**
  ```json
  {
    "status": "success",
    "project": "Candeur Lakescape",
    "micro_market": "Gachibowli",
    "commute_benchmarks": [
      {
        "origin_project": "Candeur Lakescape",
        "destination_hub": "Financial District / ADP Gachibowli",
        "distance_km": 6.8,
        "non_peak_mins": 12,
        "rush_hour_morning_mins": 20,
        "rush_hour_evening_mins": 24,
        "primary_corridor": "Via Old Mumbai Highway & Gachibowli Flyover",
        "key_intersections": ["Lingampally X Road", "Gachibowli Flyover", "ADP Junction"],
        "congestion_warning": "Fast 15-20 min direct commute to ADP Gachibowli"
      }
    ]
  }
  ```

---

### 3. `get_pricing_breakdown`
* **Description:** Retrieve an unbundled, builder-direct cost sheet showing all statutory fees, floor rise, parking, and clubhouse costs.
* **Arguments:**
  | Argument | Type | Required | Description |
  | :--- | :--- | :---: | :--- |
  | `unit_id` | `string` | Yes | Unique unit identifier (e.g. `CND-T5-1602`, `AKR-T3-1202`) |
* **Example Return:**
  ```json
  {
    "status": "success",
    "pricing_breakdown": {
      "unit_id": "CND-T5-1602",
      "project_name": "Candeur Lakescape",
      "super_built_up_sqft": 1500,
      "carpet_area_sqft": 1065,
      "base_rate_per_sqft_inr": 6100,
      "base_cost_inr": 9150000,
      "floor_rise_charges_inr": 200000,
      "corner_premium_charges_inr": 100000,
      "clubhouse_charges_inr": 400000,
      "car_parking_slots": 2,
      "car_parking_charges_inr": 600000,
      "infrastructure_and_water_inr": 350000,
      "gst_inr": 540000,
      "total_out_the_door_inr": 11340000,
      "total_in_crores": 1.134,
      "true_cost_per_carpet_sqft_inr": 10647,
      "broker_commission_inr": 0,
      "guarantee": "100% Direct Developer Pricing · Zero Broker Markup"
    }
  }
  ```

---

### 4. `get_floor_plan`
* **Description:** Retrieve architectural room-by-room measurements and usable efficiency without super built-up inflation.
* **Arguments:** `unit_id` (`string`, required)
* **Example Return:**
  ```json
  {
    "status": "success",
    "floor_plan": {
      "unit_id": "CND-T5-1602",
      "project_name": "Candeur Lakescape",
      "carpet_area_sqft": 1065,
      "usable_efficiency_pct": 71.0,
      "facing": "East",
      "rooms": [
        {"room_name": "Living & Dining", "dimensions_feet": "21'0\" x 13'0\"", "carpet_sqft": 273.0, "facing": "East"},
        {"room_name": "Master Bedroom", "dimensions_feet": "14'6\" x 12'0\"", "carpet_sqft": 174.0, "facing": "East"},
        {"room_name": "Bedroom 2", "dimensions_feet": "12'6\" x 11'6\"", "carpet_sqft": 143.7, "facing": "North"},
        {"room_name": "Bedroom 3", "dimensions_feet": "11'6\" x 11'0\"", "carpet_sqft": 126.5, "facing": "North"},
        {"room_name": "Kitchen & Utility", "dimensions_feet": "11'0\" x 8'6\"", "carpet_sqft": 93.5, "facing": "South-East"}
      ],
      "balconies": [
        {"balcony_name": "East Lakeview Deck", "dimensions_feet": "13'0\" x 5'6\"", "orientation": "East", "morning_sunlight": true}
      ]
    }
  }
  ```

---

### 5. `verify_rera`
* **Description:** Inspect official TS-RERA registration, dedicated escrow compliance, and legal litigation history.
* **Arguments:** `project_name_or_rera_id` (`string`, required)
* **Example Return:**
  ```json
  {
    "status": "success",
    "rera_verification": {
      "rera_id": "P02400005724",
      "project_name": "Candeur Lakescape",
      "developer": "Candeur Constructions",
      "sanctioning_authority": "HMDA / TS-RERA",
      "approved_towers": 7,
      "registered_handover_date": "2028-12-31",
      "status": "Under Construction - RCC Active",
      "escrow_account_compliant": true,
      "litigations_reported": 0
    }
  }
  ```

---

### 6. `compare_units`
* **Description:** Side-by-side comparative analysis of up to 5 properties on usable carpet area, cost per carpet sq ft, and commute times.
* **Arguments:** `unit_ids` (`list of strings`, required, e.g. `["ZEN-T9-0402", "CND-T5-1602"]`)

---

### 7. `save_favorite_unit`
* **Description:** Save a unit to the buyer's personalized Four Corner portfolio.
* **Arguments:** `unit_id` (`string`), `buyer_email` (`string`), `notes` (`string`, optional)

---

## 🌐 2. REST API Endpoints Reference

All MCP tools are mirrored as standard REST GET endpoints for ChatGPT Actions, web apps, and mobile integrations:

| Method | Endpoint | Query / Path Parameters | Description |
| :---: | :--- | :--- | :--- |
| `GET` | `/health` | — | Health check and protocol status |
| `GET` | `/openapi.json` | — | OpenAPI 3.1.0 schema specification |
| `GET` | `/sse` | — | Server-Sent Events MCP connection endpoint |
| `GET` | `/api/v1/properties/search` | `micro_market`, `max_budget_cr`, `bhk`, `facing`, etc. | Property discovery |
| `GET` | `/api/v1/properties/floor-plan/{unit_id}` | `unit_id` in path | Room dimensions & efficiency |
| `GET` | `/api/v1/properties/pricing/{unit_id}` | `unit_id` in path | Itemized builder cost sheet |
| `GET` | `/api/v1/properties/compare` | `unit_ids` (comma-separated) | Side-by-side comparison |
| `GET` | `/api/v1/commute/calculate` | `project_name`, `destination_hub` | Rush-hour commute times |
| `GET` | `/api/v1/rera/verify` | `query` (Project Name or RERA ID) | Official TS-RERA verification |
| `GET` | `/api/v1/admin/buyers` | — | Lead monitor for administrators |

---

## 🔐 3. OAuth 2.0 PKCE Specification

Four Corner implements RFC 7636 PKCE S256 for secure buyer authentication:

| Endpoint | Standard | Description |
| :--- | :--- | :--- |
| `GET /.well-known/oauth-authorization-server` | RFC 8414 | Discovery metadata advertising endpoints and S256 PKCE support |
| `GET /oauth/authorize` | RFC 6749 | HTML login/signup consent form (name, email, mandatory phone) |
| `POST /oauth/authorize` | RFC 6749 | Validates phone format, records user, issues authorization code |
| `POST /oauth/token` | RFC 7636 | Verifies `code_verifier` against `code_challenge` (S256), returns Bearer token |
| `GET /oauth/userinfo` | OIDC Core | Returns buyer identity (`name`, `email`, `phone`) using Bearer token |
