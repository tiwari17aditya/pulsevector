"""
Pulse Vector Operational MCP Server Launcher
Starts the standalone stdio MCP server for Antigravity IDE.
"""

import sys
import os
import pathlib

# Add src to sys.path
SRC_DIR = pathlib.Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mcp_server.server import app

if __name__ == "__main__":
    app.run(transport="stdio")
