"""
Pulse Vector Operational MCP Server (v2.5.0)
Standalone stdio JSON-RPC server providing agent-callable operational tools:
- check_quotas_and_health: Real-time quota and service health monitor
- check_content_deduplication: 90-day archive similarity & deduplication engine
- get_render_diagnostics: Media, slide, and Shorts compliance inspector
- dispatch_social_broadcast: On-demand Telegram/Discord broadcast dispatcher
- sanitize_and_redact_sensitive_data: DLP engine guaranteeing zero external secret leakage
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
from mcp_server.tools.orchestration import (
    trigger_pipeline_stage as _trigger_pipeline_stage,
    execute_autonomous_packup as _execute_autonomous_packup,
    auto_heal_environment as _auto_heal_environment,
    query_supabase_ledger as _query_supabase_ledger,
    audit_token_and_quota_ledgers as _audit_token_and_quota_ledgers,
)
from mcp_server.tools.security import (
    protect_sensitive_data,
    audit_and_sanitize_payload,
)

@app.tool()
@protect_sensitive_data
def check_quotas_and_health() -> Dict[str, Any]:
    """
    Checks operational quotas and service health across YouTube Data API,
    Gemini API, Supabase cloud database, Google Drive, and local archive storage.
    All credentials and sensitive tokens are strictly redacted.
    """
    return check_api_quotas()

@app.tool()
@protect_sensitive_data
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
@protect_sensitive_data
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
@protect_sensitive_data
def dispatch_social_broadcast(
    target_date: Optional[str] = None,
    content_type: str = "daily",
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Triggers or previews a multi-platform broadcast (Telegram & Discord) for a given date
    with native .mp4 video attachments. Webhook URLs and bot tokens are strictly protected.
    """
    return trigger_social_broadcast(target_date=target_date, content_type=content_type, dry_run=dry_run)

@app.tool()
def sanitize_and_redact_sensitive_data(payload: Any) -> Dict[str, Any]:
    """
    DLP & Security Inspection Engine:
    Inspects, redacts, and purges ANY sensitive credentials (API keys, client secrets,
    database passwords, OAuth tokens, personal emails, webhook URLs) from strings,
    dictionaries, or nested diagnostic payloads before external exposure.
    """
    return audit_and_sanitize_payload(payload)

@app.tool()
@protect_sensitive_data
def trigger_pipeline_stage(
    content_type: str = "daily",
    target_date: Optional[str] = None,
    stages: Optional[list] = None,
    dry_run: bool = False,
    force: bool = False,
    no_tts: bool = False
) -> Dict[str, Any]:
    """
    Autonomously executes a specific Pulse Vector pipeline stage (daily, weekly, monthly, brainteaser).
    Supports granular stages (text, slides, video, youtube, sync), dry-runs, and force-regeneration.
    """
    return _trigger_pipeline_stage(
        content_type=content_type,
        target_date=target_date,
        stages=stages,
        dry_run=dry_run,
        force=force,
        no_tts=no_tts
    )

@app.tool()
@protect_sensitive_data
def execute_autonomous_packup() -> Dict[str, Any]:
    """
    Executes the unified 6-phase master packup pipeline (/pulse_packup):
    System diagnostics -> Asset hierarchy -> 63-point test suite -> Storage cleaner -> Domain skills audit -> Remote Git push.
    """
    return _execute_autonomous_packup()

@app.tool()
@protect_sensitive_data
def auto_heal_environment() -> Dict[str, Any]:
    """
    Autonomously inspects and heals workspace environment anomalies:
    purges temporary render frames, validates required fonts, and verifies FFmpeg binaries.
    """
    return _auto_heal_environment()

@app.tool()
@protect_sensitive_data
def query_supabase_ledger(
    table: str = "video_uploads",
    limit: int = 10,
    date_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Read-only safe query to inspect database records in Supabase (video_uploads, daily_summaries, brain_teasers).
    """
    return _query_supabase_ledger(table=table, limit=limit, date_filter=date_filter)

@app.tool()
@protect_sensitive_data
def audit_token_and_quota_ledgers() -> Dict[str, Any]:
    """
    Audits current YouTube Data API quota budget (10k ceiling) and recent developer token logs.
    """
    return _audit_token_and_quota_ledgers()

if __name__ == "__main__":
    app.run(transport="stdio")
