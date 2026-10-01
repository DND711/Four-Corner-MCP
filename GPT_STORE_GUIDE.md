# OpenAI Plugin & GPT Migration Guide (December 11 Deadline)

> **Important Notice from OpenAI:**
> **"Custom GPTs will be retired on December 11, 2026. To keep using your tools and agents, migrate them to a Plugin."**
> 
> **The Good News:** OpenAI has unified its plugin architecture around the **Model Context Protocol (MCP)** — the exact standard Four Corner is built on. Because Four Corner exposes a remote MCP server (`/sse`), it is **100% future-proof and ready for OpenAI's new Plugin platform**.

---

## What is Changing on December 11?

1. **Retirement of Legacy Custom GPTs:** OpenAI is phasing out standalone Custom GPTs and unifying all AI extensions into the **OpenAI Plugin Directory**.
2. **MCP as the Universal Standard:** OpenAI has adopted **Model Context Protocol (MCP)** as the official engine for connected apps and tools. The same Four Corner MCP server that powers Claude and Cursor now connects natively to ChatGPT!
3. **What a 2026 Plugin Contains:**
   - **Skills:** Reusable instructions and persona guidelines.
   - **Connected App:** The **Four Corner MCP Server** (`https://<your-app>.onrender.com/sse`).
   - **Reference Files:** Optional documentation or neighborhood data.

---

## 1. Prerequisites: Deploy Four Corner to HTTPS (2 Minutes)

OpenAI's Plugin system connects to remote MCP servers over secure HTTPS (Server-Sent Events / SSE):
1. Push your latest code to GitHub: `https://github.com/DND711/Four-Corner-MCP`
2. Go to [Render.com](https://render.com) -> **New Web Service** -> Connect `Four-Corner-MCP`.
3. Choose **Docker** runtime and click **Create Web Service**.
4. You will get a live URL (e.g., `https://four-corner-mcp.onrender.com`).
   - **OpenAI & Claude MCP SSE Endpoint**: `https://four-corner-mcp.onrender.com/sse`
   - **REST / OpenAPI Schema**: `https://four-corner-mcp.onrender.com/openapi.json`
   - **Health Check**: `https://four-corner-mcp.onrender.com/health`

---

## 2. Option A: Add Four Corner as an MCP Plugin in ChatGPT (New System)

1. Open [chatgpt.com](https://chatgpt.com) and go to **Settings** -> **Developer / Connectors** (or **Plugins & Extensions**).
2. Click **"Add MCP Server"** (or **"Register Plugin"**).
3. Fill in the connection details:
   - **Plugin Name**: `Four Corner`
   - **Transport**: `SSE (Server-Sent Events)`
   - **Server URL**: `https://<your-app>.onrender.com/sse`
4. ChatGPT immediately handshakes with your live server and imports all 6 tools:
   - `search_properties`
   - `get_floor_plan`
   - `get_pricing_breakdown`
   - `calculate_commute`
   - `verify_rera`
   - `compare_units`
5. You can now chat directly in ChatGPT, and it will invoke Four Corner tools dynamically!

---

## 3. Option B: Migrate an Existing Custom GPT to a Plugin

If you already created a Custom GPT prior to the announcement:
1. Go to **"Explore GPTs"** -> **"My GPTs"** on [chatgpt.com](https://chatgpt.com).
2. Find your GPT and click **"Migrate to plugin"**.
3. OpenAI automatically transfers your system instructions into a **Skill**.
4. Under **Connected Apps**, link your Four Corner MCP endpoint:
   `https://<your-app>.onrender.com/sse`
5. Test the migration in the preview panel, then click **Save & Publish**.

---

## 4. Skill Persona & Instructions for ChatGPT

| Field | Content to Copy & Paste |
|---|---|
| **Name** | `Four Corner — Hyderabad Real Estate Intelligence` |
| **Description** | `Direct developer residential properties, verified TS-RERA filings, architectural floor plans, and ₹0 broker fee guarantee in Hyderabad.` |
| **Instructions** | *(Copy the prompt below)* |

### System Instructions:
```text
You are the Four Corner Real Estate Intelligence assistant for Hyderabad.
Your mission is to protect home buyers from misleading broker claims, undisclosed developer charges, and unverified promises.

You have access to official developer inventories in Hyderabad's prime IT and residential corridors: Kokapet, Financial District, Tellapur, Narsingi, and Gachibowli.

Operating Principles:
1. Always prioritize TRUE usable carpet area over inflated super built-up claims.
2. Break down builder cost sheets transparently (Base Rate + Floor Rise + Corner Premium + Parking + Clubhouse + GST).
3. Emphasize the Four Corner ₹0 Broker Commission guarantee: buyers pay direct developer rates.
4. Always verify TS-RERA registration, building sanctions, and designated bank escrow accounts.
5. Provide realistic peak-traffic rush-hour commute metrics (morning & evening), not midnight estimates.

Whenever the user asks to find homes, check pricing, view floor plans, compare units, or verify RERA, call the respective Four Corner Actions. Present the response with clear formatting, tables, and architectural precision.
```

### Conversation Starters:
- `Find 3 BHK corner units under ₹1.5 Cr in Kokapet or Tellapur`
- `Show me the architectural floor plan for Akrida T3-1202`
- `Break down the hidden builder costs and GST for Tellapur projects`
- `Verify TS-RERA registration and escrow account for My Home Akrida`

---

## 5. Adding Tools via OpenAPI / Actions (For Legacy or Dual Integration)

1. If your ChatGPT workspace uses Actions alongside skills:
2. Under **Schema**, you can either:
   - Click **"Import from URL"** and enter:
     `https://<your-deployed-domain>.onrender.com/openapi.json`
   - OR copy-paste the entire contents of [`chatgpt_actions_schema.json`](file:///Users/sahiththota/.gemini/antigravity-ide/scratch/four-corner-mcp/chatgpt_actions_schema.json).
3. Under **Privacy Policy**, enter:
   `https://dnd711.github.io/Four-Corner/#privacy` (or your landing page URL).
4. Under **Authentication**, select **None** (Four Corner is open and free for public buyer discovery).

---

## 6. Test and Publish to the Plugin Directory

1. In the right-hand **Preview** panel, test with a prompt:
   *"Show me units in Kokapet with direct morning sunlight."*
   ChatGPT will call your live server and display the properties!
2. Click **"Save"** or **"Publish"**.
3. Select **"Public"** (Everyone) to make it searchable in the unified **OpenAI Plugin Directory**.
4. Now, any ChatGPT user who searches "Four Corner", "Hyderabad Real Estate", or "Kokapet Apartments" can discover and add your plugin directly!
