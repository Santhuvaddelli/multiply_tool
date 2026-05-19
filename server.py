import os
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route

# 1. Initialize the MCP Server
app_server = Server("multiplier-server")

# 2. Define the multiplication tool
@app_server.list_tools()
async def handle_list_tools():
    return [
        {
            "name": "multiply_by_two",
            "description": "Multiplies a given integer by 2.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "number": {
                        "type": "integer",
                        "description": "The number to multiply"
                    }
                },
                "required": ["number"]
            }
        }
    ]

@app_server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "multiply_by_two":
        number = arguments.get("number")
        if number is None:
            raise ValueError("Missing 'number' argument")
        
        result = number * 2
        return [
            {
                "type": "text",
                "text": f"The result of {number} multiplied by 2 is {result}."
            }
        ]
    raise ValueError(f"Unknown tool: {name}")

# 3. Set up the SSE Transport endpoints for Render
sse_transport = SseServerTransport("/sse")

async def handle_sse(request):
    async with sse_transport.connect_scope(request.scope, request.receive, request._send):
        await app_server.run(
            sse_transport.read_stream,
            sse_transport.write_stream,
            app_server.create_initialization_options()
        )

async def handle_messages(request):
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)

# 4. Wrap it in a Starlette application for production hosting
app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    import uvicorn
    # Render provides a PORT environment variable dynamically
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)