import os
import mcp.types as types
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route, Mount

# MCP Server
server = Server("simple-multiplier")

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

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    number = arguments.get("number", 0)
    return [
        types.TextContent(
            type="text",
            text=str(number * 2)
        )
    ]


# SSE Transport (STABLE VERSION)
sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_sse(
        request.scope,
        request.receive,
        request._send
    ) as (read_stream, write_stream):

        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


# Starlette App
app = Starlette(
    routes=[
        Route("/sse", handle_sse, methods=["GET"]),
        Mount("/messages", app=sse.handle_post_message),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]
)

# Run
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
