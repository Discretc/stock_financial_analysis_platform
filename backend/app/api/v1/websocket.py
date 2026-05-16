"""
WebSocket endpoint for real-time stock price streaming.

Architecture:
  - Clients subscribe to specific tickers via JSON messages.
  - The server broadcasts price updates fetched from FMP every N seconds.
  - Redis pub/sub decouples producers (Celery tasks) from consumers (WS connections).
  - Each connection is isolated; disconnections are handled gracefully.
"""

import asyncio
import json
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.core.logging import get_logger
from app.services.fmp_service import fmp_client

logger = get_logger(__name__)

router = APIRouter(tags=["WebSocket"])

# Global connection registry: ticker → set of connected WebSockets
_subscriptions: dict[str, set[WebSocket]] = defaultdict(set)
_HEARTBEAT_INTERVAL = 30  # seconds
_PRICE_REFRESH_INTERVAL = 15  # seconds


class ConnectionManager:
    """Manages WebSocket lifecycle and subscription routing."""

    def subscribe(self, ticker: str, ws: WebSocket) -> None:
        _subscriptions[ticker.upper()].add(ws)
        logger.info("ws_subscribe", ticker=ticker, total=len(_subscriptions[ticker.upper()]))

    def unsubscribe(self, ticker: str, ws: WebSocket) -> None:
        _subscriptions[ticker.upper()].discard(ws)

    def unsubscribe_all(self, ws: WebSocket) -> None:
        for ticker in list(_subscriptions.keys()):
            _subscriptions[ticker].discard(ws)

    async def broadcast(self, ticker: str, payload: dict[str, Any]) -> None:
        """Send a JSON message to all subscribers of *ticker*."""
        dead: set[WebSocket] = set()
        message = json.dumps(payload)
        for ws in list(_subscriptions.get(ticker, [])):
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            _subscriptions[ticker].discard(ws)


manager = ConnectionManager()


@router.websocket("/ws/stocks/{ticker}")
async def stock_price_websocket(websocket: WebSocket, ticker: str):
    """
    WebSocket connection for real-time price updates for a single ticker.

    Message protocol:
      Client → Server: {"action": "ping"}
      Server → Client: {"type": "price", "ticker": "AAPL", "price": 182.34, ...}
      Server → Client: {"type": "pong"}
      Server → Client: {"type": "error", "message": "..."}
    """
    await websocket.accept()
    manager.subscribe(ticker, websocket)
    logger.info("ws_connected", ticker=ticker)

    # Send initial snapshot immediately
    try:
        quote = await fmp_client.get_quote(ticker)
        if quote:
            await websocket.send_json({
                "type": "price",
                "ticker": ticker.upper(),
                "price": quote.get("price"),
                "change": quote.get("change"),
                "change_percent": quote.get("changesPercentage"),
                "volume": quote.get("volume"),
                "timestamp": quote.get("timestamp"),
            })
    except Exception as exc:
        logger.warning("ws_initial_snapshot_failed", ticker=ticker, error=str(exc))

    # Background task: push price updates every _PRICE_REFRESH_INTERVAL seconds
    async def price_pusher() -> None:
        while True:
            await asyncio.sleep(_PRICE_REFRESH_INTERVAL)
            if websocket.client_state != WebSocketState.CONNECTED:
                break
            try:
                quote = await fmp_client.get_quote(ticker)
                if quote:
                    await websocket.send_json({
                        "type": "price",
                        "ticker": ticker.upper(),
                        "price": quote.get("price"),
                        "change": quote.get("change"),
                        "change_percent": quote.get("changesPercentage"),
                        "volume": quote.get("volume"),
                        "timestamp": quote.get("timestamp"),
                    })
            except Exception as exc:
                logger.warning("ws_push_failed", ticker=ticker, error=str(exc))
                break

    # Background heartbeat
    async def heartbeat() -> None:
        while True:
            await asyncio.sleep(_HEARTBEAT_INTERVAL)
            if websocket.client_state != WebSocketState.CONNECTED:
                break
            try:
                await websocket.send_json({"type": "ping"})
            except Exception:
                break

    price_task = asyncio.create_task(price_pusher())
    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                if msg.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass  # Ignore malformed messages
    except WebSocketDisconnect:
        logger.info("ws_disconnected", ticker=ticker)
    finally:
        price_task.cancel()
        heartbeat_task.cancel()
        manager.unsubscribe(ticker, websocket)
