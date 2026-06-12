import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse


router = APIRouter(tags=["sse"])

# Simple in-memory broadcaster for Phase 1
# In a real distributed system, use Redis Pub/Sub
class EventBroadcaster:
    def __init__(self):
        self.clients: set[asyncio.Queue] = set()

    async def publish(self, event_type: str, data: dict):
        payload = json.dumps(data)
        message = f"event: {event_type}\ndata: {payload}\n\n"
        # Push to all connected clients
        for queue in list(self.clients):
            await queue.put(message)

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self.clients.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self.clients:
            self.clients.remove(q)

broadcaster = EventBroadcaster()

async def event_generator(request: Request) -> AsyncGenerator[str, None]:
    q = broadcaster.subscribe()
    try:
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break
            
            # Wait for a message or a timeout to keep connection alive
            try:
                message = await asyncio.wait_for(q.get(), timeout=15.0)
                yield message
            except asyncio.TimeoutError:
                # Keep-alive ping
                yield ": ping\n\n"
    finally:
        broadcaster.unsubscribe(q)

@router.get("/web/stream-events")
async def stream_events(request: Request):
    """
    SSE endpoint for real-time updates to the UI.
    """
    return StreamingResponse(
        event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # For Nginx if used
        }
    )

@router.post("/api/admin/broadcast-test", include_in_schema=False)
async def broadcast_test(event_type: str, message: str):
    """
    Simple test endpoint to manually trigger a broadcast.
    """
    await broadcaster.publish(event_type, {"message": message})
    return {"status": "broadcasted"}
