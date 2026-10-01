# Four Corner MCP Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Spec](https://img.shields.io/badge/MCP-2.2.0-green.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Property Intelligence & Verified Real Estate Discovery for AI Assistants.**  
> Direct access to official developer records, true architectural carpet areas, transparent builder pricing, and live rush-hour commute data in West Hyderabad — completely broker-free.

---

## Overview

Traditional property portals are cluttered with fabricated rates, inflated super built-up areas, and broker middlemen harvesting contact numbers.

**Four Corner** connects LLMs (Claude Desktop, ChatGPT, Cursor, Windsurf) directly to verified builder ERP inventories and official Telangana RERA filings via the **Model Context Protocol (MCP)**.

### Guaranteed Core Principles:
- **Zero Brokers**: Connect directly to official developer pricing with zero commission markup.
- **True Carpet Area**: Room-by-room architectural blueprint measurements without inflated builder math.
- **Strict Budget Integrity**: If your ceiling is ₹1.4 Cr, you will never see a property above ₹1.4 Cr.
- **Live Commute Benchmarks**: Realistic rush-hour drive times to Financial District, HITEC City, Kokapet SEZ, and RGIA Airport.

---

## MCP Tools Reference

The server exposes 6 high-precision tools:

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| `search_properties` | `micro_market`, `min_budget_cr`, `max_budget_cr`, `bhk`, `facing`, `corner_only`, `morning_sunlight_only`, `ready_by_year`, `min_carpet_sqft` | Filter verified residential inventory strictly by your criteria. |
| `get_floor_plan` | `unit_id` | Room-by-room dimensions, true usable carpet ratio, and balcony orientations. |
| `get_pricing_breakdown` | `unit_id` | Complete builder cost sheet: base rate, floor rise, parking, clubhouse, GST, and true cost per carpet sq ft. |
| `calculate_commute` | `project_id_or_name`, `destination_hub` | Peak rush-hour morning & evening drive times and arterial bottleneck alerts. |
| `verify_rera` | `project_name_or_rera_id` | Official TS-RERA registration, sanction orders, escrow accounts, and compliance health. |
| `compare_units` | `unit_ids` | Side-by-side comparative analysis of efficiency, carpet rate, and delivery dates. |

---

## Quickstart

### 1. Installation

Clone and set up with Python 3.11+:

```bash
cd /Users/sahiththota/.gemini/antigravity-ide/scratch/four-corner-mcp
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Run Test Suite

Verify all tools and database queries:

```bash
pytest -v
```

## Cloud Hosting & AI Website Integration

Four Corner runs in dual-mode:
1. **Local Mode (`stdio`)**: For local Claude Desktop, Cursor, and Windsurf clients.
2. **Cloud Web Service (`SSE` + REST)**: Hosts both Claude Server-Sent Events (SSE) and ChatGPT Custom GPT Actions simultaneously.

---

### 🌐 1. Deploying to the Cloud (Free 24/7 Hosting)

The repository includes a ready-to-deploy `Dockerfile` and `render.yaml`.

#### Option A: 1-Click Deploy on Render
1. Push this repository to your GitHub account: `https://github.com/DND711/Four-Corner-MCP`.
2. Go to [Render.com](https://render.com) -> **New Web Service** -> Select `Four-Corner-MCP`.
3. Render detects the Dockerfile and deploys it automatically.
4. Your server will be live at:
   - **OpenAPI Schema (for ChatGPT)**: `https://<your-app>.onrender.com/openapi.json`
   - **Claude MCP SSE Endpoint**: `https://<your-app>.onrender.com/sse`
   - **Health Check**: `https://<your-app>.onrender.com/health`

#### Option B: Run Cloud Server Locally
```bash
python -m four_corner.server --sse --port 8000
```

---

### 🤖 2. ChatGPT Store (Plugin Store / Custom GPT)

Four Corner can be published to the global **ChatGPT Store** so anyone on ChatGPT can search, install, and use it directly.

- **Full Step-by-Step Guide**: See [GPT_STORE_GUIDE.md](file:///Users/sahiththota/.gemini/antigravity-ide/scratch/four-corner-mcp/GPT_STORE_GUIDE.md)
- **OpenAPI Spec File**: [chatgpt_actions_schema.json](file:///Users/sahiththota/.gemini/antigravity-ide/scratch/four-corner-mcp/chatgpt_actions_schema.json)

**Quick Setup in ChatGPT:**
1. Open [chatgpt.com](https://chatgpt.com) -> **Explore GPTs** -> **+ Create**.
2. Go to the **Configure** tab -> Add Name, Description, and Instructions.
3. Scroll to **Actions** -> Click **Create new action** -> **Import from URL** -> Paste your `https://<your-app>.onrender.com/openapi.json`.
4. Click **Publish to Everyone** (The Public GPT Store).

---

### 🔮 3. Claude & Public MCP Directory Discovery

- **Full Step-by-Step Guide**: See [CLAUDE_DIRECTORY_GUIDE.md](file:///Users/sahiththota/.gemini/antigravity-ide/scratch/four-corner-mcp/CLAUDE_DIRECTORY_GUIDE.md)
- **Smithery Registry Manifest**: [smithery.yaml](file:///Users/sahiththota/.gemini/antigravity-ide/scratch/four-corner-mcp/smithery.yaml)

#### Discoverable on Smithery.ai:
1. Submit your repo at [smithery.ai](https://smithery.ai).
2. Users can 1-click install into Claude Desktop or run:
   ```bash
   npx -y @smithery/cli install @DND711/Four-Corner-MCP --client claude
   ```

#### Remote Claude Connection (Zero Local Setup):
Claude users can connect to your remote cloud server directly via SSE without running code on their local machine:
```json
{
  "mcpServers": {
    "four-corner": {
      "url": "https://<your-app>.onrender.com/sse"
    }
  }
}
```

---

## Local Client Integration (Desktop & Editors)

### Claude Desktop Configuration (Local stdio)

Add the following entry to your `claude_desktop_config.json`:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "four-corner": {
      "command": "/Users/sahiththota/.gemini/antigravity-ide/scratch/four-corner-mcp/.venv/bin/four-corner-mcp",
      "args": []
    }
  }
}
```

### Cursor / Windsurf Configuration

Add to your project's `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "four-corner": {
      "command": "/Users/sahiththota/.gemini/antigravity-ide/scratch/four-corner-mcp/.venv/bin/four-corner-mcp"
    }
  }
}
```

---

## Example Prompts to Ask Your AI

Once connected in Claude or ChatGPT:

- *"Find me 3BHK corner units in Kokapet or Tellapur under ₹1.5 Cr ready before 2026 with east-facing balconies."*
- *"Show me the true carpet efficiency and master bedroom dimensions for unit AKR-T3-1202."*
- *"What will my actual morning rush-hour drive time be from My Home Akrida to Waverock in Financial District?"*
- *"Give me the complete builder pricing breakdown for TRK-T2-1801 including GST and floor rise."*
- *"Verify RERA registration and escrow compliance for P02400005128."*

---

## License

MIT License. Designed & Built for the Four Corner Property Intelligence ecosystem.

