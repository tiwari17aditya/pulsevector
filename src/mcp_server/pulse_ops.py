"""
Pulse Vector Operational MCP & Diagnostic Control Plane (v2.5.1)
Standalone module exporting operational diagnostics, health checks,
and MCP tools for both GitHub Actions workflows and local agents.
"""

import sys
import pathlib
import datetime
from typing import Dict, Any, Optional

# Ensure both project root and src/ are on sys.path
_CURRENT_DIR = pathlib.Path(__file__).resolve().parent
_SRC_DIR = _CURRENT_DIR.parent
_ROOT_DIR = _SRC_DIR.parent

for p in (str(_SRC_DIR), str(_ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from mcp_server.tools.quotas import check_api_quotas
from mcp_server.tools.deduplication import query_content_deduplication
from mcp_server.tools.diagnostics import inspect_render_diagnostics
from mcp_server.tools.broadcast import trigger_social_broadcast
from mcp_server.tools.orchestration import (
    trigger_pipeline_stage,
    execute_autonomous_packup,
    auto_heal_environment,
    query_supabase_ledger,
    audit_token_and_quota_ledgers,
)
from mcp_server.tools.security import audit_and_sanitize_payload, protect_sensitive_data


def get_health_and_quotas_summary() -> Dict[str, Any]:
    """
    Computes real-time health and quota diagnostic payload across all Pulse Vector services.
    Returns a unified dict containing both structured service status and summary keys
    ('overall_health' and 'checks') expected by GitHub Actions workflows and IDE agents.
    """
    raw = check_api_quotas()

    yt_status = raw.get("youtube_api", {}).get("status", "UNKNOWN")
    storage_status = raw.get("storage", {}).get("status", "UNKNOWN")
    gemini_configured = raw.get("gemini_api", {}).get("configured", False)
    supabase_configured = raw.get("supabase_cloud", {}).get("configured", False)
    supabase_connected = raw.get("supabase_cloud", {}).get("connected", False)

    overall = "HEALTHY"
    if storage_status == "LOW_DISK_SPACE" or yt_status == "WARNING":
        overall = "WARNING"
    elif yt_status == "EXHAUSTED" or not gemini_configured:
        overall = "DEGRADED"

    checks = {
        "gemini_api": {
            "status": "PASS" if gemini_configured else "WARN",
            "configured": gemini_configured,
            "details": raw.get("gemini_api", {})
        },
        "youtube_api": {
            "status": yt_status,
            "details": raw.get("youtube_api", {})
        },
        "supabase_cloud": {
            "status": "PASS" if supabase_connected else ("WARN" if supabase_configured else "INFO"),
            "connected": supabase_connected,
            "details": raw.get("supabase_cloud", {})
        },
        "google_drive_cloud": {
            "status": raw.get("google_drive_cloud", {}).get("status", "UNKNOWN"),
            "details": raw.get("google_drive_cloud", {})
        },
        "storage": {
            "status": storage_status,
            "details": raw.get("storage", {})
        }
    }

    result = dict(raw)
    result["overall_health"] = overall
    result["checks"] = checks
    return result


async def check_quotas_and_health() -> Dict[str, Any]:
    """
    Asynchronous diagnostic checker for pre-flight health assessment.
    Designed for `asyncio.run(check_quotas_and_health())` in GitHub Actions.
    """
    return get_health_and_quotas_summary()


def check_quotas_and_health_sync() -> Dict[str, Any]:
    """Synchronous diagnostic checker for IDE agents and scripts."""
    return get_health_and_quotas_summary()


# Export standard operational tools
def check_content_deduplication(
    query: str,
    lookback_days: int = 90,
    content_type: str = "all"
) -> Dict[str, Any]:
    return query_content_deduplication(query, lookback_days=lookback_days, content_type=content_type)


def get_render_diagnostics(
    target_date: Optional[str] = None,
    content_type: str = "daily"
) -> Dict[str, Any]:
    return inspect_render_diagnostics(target_date=target_date, content_type=content_type)


def dispatch_social_broadcast(
    target_date: Optional[str] = None,
    content_type: str = "daily",
    dry_run: bool = True
) -> Dict[str, Any]:
    return trigger_social_broadcast(target_date=target_date, content_type=content_type, dry_run=dry_run)


def sanitize_and_redact_sensitive_data(payload: Any) -> Dict[str, Any]:
    return audit_and_sanitize_payload(payload)


__all__ = [
    "check_quotas_and_health",
    "check_quotas_and_health_sync",
    "get_health_and_quotas_summary",
    "check_content_deduplication",
    "get_render_diagnostics",
    "dispatch_social_broadcast",
    "trigger_pipeline_stage",
    "execute_autonomous_packup",
    "auto_heal_environment",
    "query_supabase_ledger",
    "audit_token_and_quota_ledgers",
    "sanitize_and_redact_sensitive_data",
]
