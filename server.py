import os
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route, Mount

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

# 3. Create the SSE transport instance mapping to '/messages'
sse_transport = SseServerTransport("/messages")

# 4. Correctly handle the SSE endpoint using connect_sse
async def handle_sse(request):
    async with sse_transport.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await app_server.run(
            read_stream,
            write_stream,
            app_server.create_initialization_options()
        )

# 5. Enable CORS middleware so your local browser/Inspector can connect safely
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows the MCP Inspector on localhost to talk to Render
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
]

# 6. Build the Starlette App
# Note: sse_transport.handle_post_message acts as its own ASGI app for the Mount route
app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages", app=sse_transport.handle_post_message),
    ],
    middleware=middleware
)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
