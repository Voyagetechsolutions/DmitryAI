# agent/__init__.py
"""
Dmitry Agent - Local API server for UI communication.

The Electron UI connects to this server via localhost.
"""

from .server import AgentServer

__all__ = ["AgentServer"]
