# How to Publish Four Corner to the ChatGPT Store (Custom GPT)

You can publish **Four Corner** as a verified, publicly searchable app in the **ChatGPT Store** (formerly Plugin Store) so anyone on ChatGPT can search, install, and chat with it.

---

## 1. Prerequisites (2 Minutes Setup)
Your Four Corner server must be accessible via HTTPS. You can deploy it for free to **Render.com** or **Railway.app** using the included `Dockerfile` and `render.yaml`:
1. Push your latest code to GitHub: `https://github.com/DND711/Four-Corner-MCP`
2. Go to [Render.com](https://render.com) -> **New Web Service** -> Connect `Four-Corner-MCP`.
3. Choose **Docker** runtime and click **Create Web Service**.
4. You will get a live URL (e.g., `https://four-corner-mcp.onrender.com`).
   - Your OpenAPI Schema is immediately live at: `https://four-corner-mcp.onrender.com/openapi.json`
   - Your Claude MCP SSE endpoint is at: `https://four-corner-mcp.onrender.com/sse`

---

## 2. Creating the Custom GPT in ChatGPT

1. Open [chatgpt.com](https://chatgpt.com) and log in.
2. In the left sidebar, click **"Explore GPTs"** (The GPT Store).
3. In the top right corner, click **"+ Create"** to open the GPT Builder.
4. Click on the **"Configure"** tab.

---

## 3. Fill in the Profile Details

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

## 4. Add the Four Corner Actions (API Integration)

1. Scroll down to the **Actions** section at the bottom of the Configure tab.
2. Click **"Create new action"**.
3. Under **Schema**, you can either:
   - Click **"Import from URL"** and enter:
     `https://<your-deployed-domain>.onrender.com/openapi.json`
   - OR copy-paste the entire contents of [`chatgpt_actions_schema.json`](file:///Users/sahiththota/.gemini/antigravity-ide/scratch/four-corner-mcp/chatgpt_actions_schema.json).
4. Under **Privacy Policy**, enter:
   `https://dnd711.github.io/Four-Corner/#privacy` (or your landing page URL).
5. Under **Authentication**, select **None** (Four Corner is open and free for public buyer discovery).

---

## 5. Test and Publish to the Store

1. In the right-hand **Preview** panel, test with a prompt:
   *"Show me units in Kokapet with direct morning sunlight."*
   ChatGPT will call your live server action and display the properties!
2. In the top right corner, click **"Create"** or **"Update"**.
3. Select **"Public"** (Everyone) to publish it to the global **ChatGPT Store**.
4. Now, any ChatGPT user who searches "Four Corner", "Hyderabad Real Estate", or "Kokapet Apartments" in the GPT Store can discover and use your assistant directly!
