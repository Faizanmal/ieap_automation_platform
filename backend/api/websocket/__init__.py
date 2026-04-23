"""
WebSocket Real-Time Communication Hub

Enterprise-grade WebSocket implementation for real-time updates,
streaming predictions, notifications, and live dashboard feeds.
"""

from .manager import WebSocketManager
from .router import websocket_router

__all__ = ["WebSocketManager", "websocket_router"]
