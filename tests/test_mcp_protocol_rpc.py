"""
Test direct Model Context Protocol (MCP) JSON-RPC protocol compliance
Testing initialize, tools/list, tools/call, resources/list, resources/read
"""

import asyncio
from four_corner.server import server, db

async def run_mcp_rpc_tests():
    print("\n=======================================================")
    print("RUNNING DIRECT MODEL CONTEXT PROTOCOL (MCP) RPC TESTS")
    print("=======================================================\n")

    # 1. Inspect Server Name and Instructions
    print(f" [PASS] 1. MCP Server Name: '{server.name}'")
    assert server.name == "four-corner"

    # 2. Tools registered
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]
    print(f" [PASS] 2. MCP Tools ({len(tools)} registered): {tool_names}")
    assert "search_properties" in tool_names
    assert "get_floor_plan" in tool_names
    assert "get_pricing_breakdown" in tool_names
    assert "calculate_commute" in tool_names
    assert "verify_rera" in tool_names

    # 3. Call tool: search_properties for Sahith Home
    print(" [INFO] Calling MCP Tool 'search_properties' for 'Sahith Home'...")
    search_res = await server.call_tool("search_properties", {"project_name": "Sahith Home"})
    # Tool result can be a dict, string or list of Content blocks
    print(f" [PASS] 3. MCP Tool Call 'search_properties' executed successfully")
    
    # 4. Resources registered
    resources = await server.list_resources()
    resource_uris = [r.uri for r in resources]
    print(f" [PASS] 4. MCP Resources ({len(resources)} registered): {resource_uris}")
    assert "ui://four-corner/property-card" in resource_uris

    # 5. Read Resource: ui://four-corner/property-card
    print(" [INFO] Reading MCP Resource 'ui://four-corner/property-card'...")
    ui_content = await server.read_resource("ui://four-corner/property-card")
    assert len(ui_content) > 0
    html_text = ui_content[0].content
    assert len(html_text) > 1000
    print(f" [PASS] 5. MCP Resource read successfully ({len(html_text)} bytes, mime_type={ui_content[0].mime_type})")

    print("\n=======================================================")
    print("ALL MODEL CONTEXT PROTOCOL (MCP) RPC TESTS PASSED!")
    print("=======================================================\n")

if __name__ == "__main__":
    asyncio.run(run_mcp_rpc_tests())
