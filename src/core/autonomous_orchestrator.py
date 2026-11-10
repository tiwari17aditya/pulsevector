"""
Pulse Vector - Autonomous AI Orchestrator Engine (v3.0.0)
Coordinates fully autonomous end-to-end execution of:
1. Operational Pre-flight & Self-Healing
2. Archive Similarity & News/Teaser Deduplication
3. Daily / Weekly / Monthly / Brain Teaser Pipeline Execution
4. Shorts Compliance & Video Render Diagnostics
5. YouTube Data API Publishing & Pinned Comment Engagement
6. Multi-Platform Social Broadcasting (Telegram & Discord)
7. Cloud DB & Google Drive Archive Sync
8. Quota & Token Ledger Maintenance
9. Master Packup & Git Remote Synchronization
"""

import os
import sys
import logging
import pathlib
import datetime
from typing import Dict, Any, List, Optional

_CURRENT_DIR = pathlib.Path(__file__).resolve().parent
_SRC_DIR = _CURRENT_DIR.parent
_ROOT_DIR = _SRC_DIR.parent

for p in (str(_SRC_DIR), str(_ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from core.config import current_date_str, ARCHIVE_DIR
from mcp_server.tools.quotas import check_api_quotas
from mcp_server.tools.deduplication import query_content_deduplication
from mcp_server.tools.diagnostics import inspect_render_diagnostics
from mcp_server.tools.broadcast import trigger_social_broadcast
from mcp_server.tools.orchestration import (
    trigger_pipeline_stage,
    execute_autonomous_packup,
    auto_heal_environment,
    audit_token_and_quota_ledgers,
)

logger = logging.getLogger("autonomous_orchestrator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class AutonomousOrchestrator:
    """
    Unified AI Control Plane for fully autonomous channel operation.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.root_dir = _ROOT_DIR
        self.report: Dict[str, Any] = {
            "orchestrator_version": "3.0.0",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dry_run": self.dry_run,
            "phases": {},
            "status": "INITIALIZED"
        }

    def run_preflight_diagnostics(self) -> Dict[str, Any]:
        """
        Phase 1: Validates infrastructure, quotas, and applies auto-healing.
        """
        logger.info("Executing Phase 1: Pre-flight Diagnostics & Environment Auto-Healing...")
        healing_result = auto_heal_environment()
        quota_result = check_api_quotas()
        
        yt_status = quota_result.get("youtube_api", {}).get("status", "UNKNOWN")
        can_upload_youtube = (yt_status != "EXHAUSTED")
        
        preflight_data = {
            "status": "HEALTHY" if healing_result.get("status") == "HEALTHY" else "WARNING",
            "healing": healing_result,
            "quotas": quota_result,
            "can_upload_youtube": can_upload_youtube
        }
        self.report["phases"]["preflight"] = preflight_data
        return preflight_data

    def check_content_uniqueness(self, candidate_topics: List[str], content_type: str = "news") -> List[Dict[str, Any]]:
        """
        Phase 2: Runs 90-day archive deduplication against candidate headlines/topics.
        """
        logger.info("Executing Phase 2: Content Deduplication Screening...")
        results = []
        for topic in candidate_topics:
            dedup_res = query_content_deduplication(topic, lookback_days=90, content_type=content_type)
            results.append(dedup_res)
        return results

    def execute_daily_pipelines(self, target_date: Optional[datetime.datetime] = None, force: bool = False) -> Dict[str, Any]:
        """
        Phase 3: Executes Daily Current Affairs & Daily Brain Teaser pipelines.
        """
        dt = target_date or datetime.datetime.now()
        dt_str = dt.strftime("%Y-%m-%d")
        logger.info(f"Executing Phase 3: Daily Pipelines for {dt_str} (dry_run={self.dry_run})...")
        
        daily_res = trigger_pipeline_stage(
            content_type="daily",
            target_date=dt_str,
            dry_run=self.dry_run,
            force=force
        )
        
        teaser_res = trigger_pipeline_stage(
            content_type="brainteaser",
            target_date=dt_str,
            dry_run=self.dry_run,
            force=force
        )
        
        # Check weekly trigger (Sunday = 6)
        weekly_res = None
        if dt.weekday() == 6:
            logger.info("Sunday detected: Triggering Weekly Masterclass pipeline...")
            weekly_res = trigger_pipeline_stage(
                content_type="weekly",
                target_date=dt_str,
                dry_run=self.dry_run,
                force=force
            )
            
        # Check monthly trigger (month-end)
        monthly_res = None
        is_month_end = (dt + datetime.timedelta(days=1)).month != dt.month
        if is_month_end:
            logger.info("Month-end detected: Triggering Monthly Masterclass pipeline...")
            monthly_res = trigger_pipeline_stage(
                content_type="monthly",
                target_date=dt_str,
                dry_run=self.dry_run,
                force=force
            )
            
        execution_data = {
            "daily_current_affairs": daily_res,
            "daily_brain_teaser": teaser_res,
            "weekly_masterclass": weekly_res,
            "monthly_masterclass": monthly_res
        }
        self.report["phases"]["pipelines"] = execution_data
        return execution_data

    def verify_render_diagnostics(self, target_date: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """
        Phase 4: Inspects rendered assets and Shorts duration compliance.
        """
        dt = target_date or datetime.datetime.now()
        dt_str = dt.strftime("%Y-%m-%d")
        logger.info(f"Executing Phase 4: Render Diagnostics for {dt_str}...")
        
        diag_daily = inspect_render_diagnostics(target_date=dt_str, content_type="daily")
        diag_teaser = inspect_render_diagnostics(target_date=dt_str, content_type="brainteaser")
        
        render_data = {
            "daily_diagnostics": diag_daily,
            "teaser_diagnostics": diag_teaser
        }
        self.report["phases"]["diagnostics"] = render_data
        return render_data

    def dispatch_broadcasts(self, target_date: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """
        Phase 5: Broadcasts to Telegram and Discord channels.
        """
        dt = target_date or datetime.datetime.now()
        dt_str = dt.strftime("%Y-%m-%d")
        logger.info(f"Executing Phase 5: Social Broadcasts for {dt_str} (dry_run={self.dry_run})...")
        
        broadcast_daily = trigger_social_broadcast(
            target_date=dt_str,
            content_type="daily",
            dry_run=self.dry_run
        )
        broadcast_teaser = trigger_social_broadcast(
            target_date=dt_str,
            content_type="brainteaser",
            dry_run=self.dry_run
        )
        
        broadcast_data = {
            "daily_broadcast": broadcast_daily,
            "teaser_broadcast": broadcast_teaser
        }
        self.report["phases"]["broadcasts"] = broadcast_data
        return broadcast_data

    def execute_postflight_and_packup(self) -> Dict[str, Any]:
        """
        Phase 6: Audits ledgers and executes master sign-off & remote git synchronization.
        """
        logger.info("Executing Phase 6: Post-flight Audits & Master Packup Synchronization...")
        ledgers = audit_token_and_quota_ledgers()
        
        if self.dry_run:
            packup_result = {
                "status": "SKIPPED_DRY_RUN",
                "message": "Packup and Git push skipped during dry-run validation."
            }
        else:
            packup_result = execute_autonomous_packup()
            
        postflight_data = {
            "ledgers": ledgers,
            "packup": packup_result
        }
        self.report["phases"]["postflight"] = postflight_data
        return postflight_data

    def run_full_autonomous_cycle(
        self,
        target_date: Optional[datetime.datetime] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Runs the complete, autonomous cycle hands-free.
        """
        start_time = datetime.datetime.now()
        logger.info("=========================================================")
        logger.info("  🚀 PULSE VECTOR AUTONOMOUS AI ORCHESTRATOR CYCLE")
        logger.info(f"  Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  Mode: {'DRY RUN' if self.dry_run else 'PRODUCTION LIVE'}")
        logger.info("=========================================================")

        try:
            # 1. Preflight
            preflight = self.run_preflight_diagnostics()
            
            # 2. Pipeline execution
            pipelines = self.execute_daily_pipelines(target_date=target_date, force=force)
            
            # 3. Diagnostics
            diagnostics = self.verify_render_diagnostics(target_date=target_date)
            
            # 4. Social Broadcast
            broadcasts = self.dispatch_broadcasts(target_date=target_date)
            
            # 5. Postflight & Packup
            postflight = self.execute_postflight_and_packup()
            
            total_duration = (datetime.datetime.now() - start_time).total_seconds()
            self.report["duration_seconds"] = round(total_duration, 2)
            self.report["status"] = "COMPLETED_SUCCESSFULLY"
            
            logger.info("=========================================================")
            logger.info("  ✅ AUTONOMOUS CYCLE COMPLETED SUCCESSFULLY")
            logger.info(f"  Duration: {self.report['duration_seconds']}s")
            logger.info("=========================================================")
            return self.report

        except Exception as ex:
            logger.error(f"❌ Autonomous cycle failed with error: {ex}", exc_info=True)
            self.report["status"] = "FAILED"
            self.report["error"] = str(ex)
            return self.report


def execute_cycle_now(dry_run: bool = False, force: bool = False) -> Dict[str, Any]:
    """Helper entry point for scripts and agents."""
    orchestrator = AutonomousOrchestrator(dry_run=dry_run)
    return orchestrator.run_full_autonomous_cycle(force=force)
