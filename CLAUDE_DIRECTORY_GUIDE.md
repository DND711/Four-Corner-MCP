# How to List Four Corner in Claude & Public MCP Registries

Anthropic's **Model Context Protocol (MCP)** allows Claude Desktop, Cursor, and web clients to connect to remote MCP servers. By registering Four Corner in public MCP directories, Claude users worldwide can discover, search, and 1-click install your server.

---

## 1. Discoverable via Smithery.ai (The App Store for Claude MCPs)

[Smithery.ai](https://smithery.ai) is the leading registry for MCP servers. When your repository has a `smithery.yaml` file (which is already included in this repo), it can be indexed immediately:

### How to Index on Smithery:
1. Ensure your repository is public: [https://github.com/DND711/Four-Corner-MCP](https://github.com/DND711/Four-Corner-MCP)
2. Visit [smithery.ai](https://smithery.ai) and sign in with GitHub.
3. Click **"Submit Server"** and paste your GitHub repository URL:
   `https://github.com/DND711/Four-Corner-MCP`
4. Smithery reads `smithery.yaml`, verifies your tools (`search_properties`, `get_floor_plan`, `get_pricing_breakdown`, `calculate_commute`, `verify_rera`, `compare_units`), and lists **Four Corner** in their public directory.

### What Claude Users Experience:
- Users searching for *"Real Estate"*, *"Hyderabad"*, or *"Four Corner"* on Smithery can install it with **1 click**.
- Or run in terminal:
  ```bash
  npx -y @smithery/cli install @DND711/Four-Corner-MCP --client claude
  ```
  This automatically registers Four Corner into their Claude configuration!

---

## 2. Remote SSE Connection (Direct Web-to-Claude Hosting)

Claude also supports connecting directly to cloud-hosted MCP servers over **Server-Sent Events (SSE)** without running anything locally on the user's laptop.

Once your server is deployed to Render, Railway, or Fly.io:
1. Your public SSE URL is:
   `https://<your-deployed-domain>.onrender.com/sse`
2. In the Claude Desktop configuration (`claude_desktop_config.json`) or remote web client, users simply add:
   ```json
   {
     "mcpServers": {
       "four-corner": {
         "url": "https://<your-deployed-domain>.onrender.com/sse"
       }
     }
   }
   ```
3. Claude automatically discovers all 6 tools from the cloud server and displays the hammer  tool icon in chat!

---

## 3. Glama.ai Directory Listing

[Glama.ai](https://glama.ai/mcp/servers) is another major directory for Claude MCP servers.
- Submit `https://github.com/DND711/Four-Corner-MCP` to Glama to be featured in the Real Estate & Property Discovery category.
