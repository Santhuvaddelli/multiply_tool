import os
import asyncio
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response

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

# 3. Create the SSE transport global instance
sse_transport = SseServerTransport("/messages")

# 4. Handle the continuous SSE GET stream
async def handle_sse(request):
    async def sse_stream_generator():
        # This keeps the connection open and streams data to the client
        async for message in sse_transport.connect_scope(request.scope, request.receive, request._send):
            yield message

    # Run the MCP server engine in the background for this stream
    asyncio.create_task(
        app_server.run(
            sse_transport.read_stream,
            sse_transport.write_stream,
            app_server.create_initialization_options()
        )
    )
    
    # Return standard SSE headers
    return Response(
        sse_stream_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # Crucial for cloud platforms like Render
        }
    )

# 5. Handle the incoming HTTP POST messages from the inspector/client
async def handle_messages(request):
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)
    return Response("Message received", status_code=202)

# 6. Starlette Application Setup
app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
