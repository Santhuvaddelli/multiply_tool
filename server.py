import os
import mcp.types as types
from mcp.server import Server
from mcp.server.streamable_http import StreamableHttpServerTransport
from starlette.applications import Starlette
from starlette.routing import Route

# -------------------------
# MCP SERVER
# -------------------------
server = Server("simple-multiplier")

# LIST TOOLS
@server.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="multiply_by_two",
            description="Multiply a number by 2",
            inputSchema={
                "type": "object",
                "properties": {
                    "number": {"type": "integer"}
                },
                "required": ["number"]
            }
        )
    ]

# CALL TOOL
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name != "multiply_by_two":
        raise ValueError("Unknown tool")

    number = arguments.get("number", 0)
    result = number * 2

    return [
        types.TextContent(
            type="text",
            text=str(result)
        )
    ]


# -------------------------
# STREAMABLE HTTP
# -------------------------
transport = StreamableHttpServerTransport(server, path="/mcp")

app = Starlette(
    routes=[
        Route("/mcp", transport.handle_request, methods=["GET", "POST"]),
    ]
)

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
