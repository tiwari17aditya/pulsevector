"""
Pulse Vector Operational MCP Server (v2.5.0)
Standalone stdio JSON-RPC server providing agent-callable operational tools:
- check_quotas_and_health: Real-time quota and service health monitor
- check_content_deduplication: 90-day archive similarity & deduplication engine
- get_render_diagnostics: Media, slide, and Shorts compliance inspector
- dispatch_social_broadcast: On-demand Telegram/Discord broadcast dispatcher
"""

import sys
import pathlib

# Ensure src/ is on sys.path
SRC_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from typing import Dict, Any, Optional

try:
    from mcp.server.mcpserver import MCPServer
    app = MCPServer("pulse-ops-mcp")
except Exception:
    class DummyMCPServer:
        def tool(self):
            def decorator(f):
                return f
            return decorator
        def run(self, *args, **kwargs):
            pass
    app = DummyMCPServer()

from mcp_server.tools.quotas import check_api_quotas
from mcp_server.tools.deduplication import query_content_deduplication
from mcp_server.tools.diagnostics import inspect_render_diagnostics
from mcp_server.tools.broadcast import trigger_social_broadcast

@app.tool()
def check_quotas_and_health() -> Dict[str, Any]:
    """
    Checks operational quotas and service health across YouTube Data API,
    Gemini API, Supabase cloud database, Google Drive, and local archive storage.
    """
    return check_api_quotas()

@app.tool()
def check_content_deduplication(
    query: str,
    lookback_days: int = 90,
    content_type: str = "all"
) -> Dict[str, Any]:
    """
    Scans past 90 days of Pulse Vector Current Affairs and Brain Teasers to prevent
    topic repetition, recycling puzzle formulas, or duplicate news generation.
    """
    return query_content_deduplication(query, lookback_days=lookback_days, content_type=content_type)

@app.tool()
def get_render_diagnostics(
    target_date: Optional[str] = None,
    content_type: str = "daily"
) -> Dict[str, Any]:
    """
    Inspects pipeline assets, slide cards, audio alignment, and compiled video
    duration for a specific date and content type.
    """
    return inspect_render_diagnostics(target_date=target_date, content_type=content_type)

@app.tool()
def dispatch_social_broadcast(
    target_date: Optional[str] = None,
    content_type: str = "daily",
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Triggers or previews a multi-platform broadcast (Telegram & Discord) for a given date
    with native .mp4 video attachments.
    """
    return trigger_social_broadcast(target_date=target_date, content_type=content_type, dry_run=dry_run)

if __name__ == "__main__":
    app.run(transport="stdio")
