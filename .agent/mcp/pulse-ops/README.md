# ⚡ Pulse Vector Operational MCP Server (`pulse-ops-mcp`)

**Version:** 2.5.0  
**Transport:** Stdio (JSON-RPC 2.0)  
**Launcher:** `python scripts/run_pulse_mcp.py`  

The Pulse Vector Operational MCP Server exposes high-leverage operational, diagnostic, and monitoring capabilities to the AI agent in Antigravity IDE. It bridges local project execution with live cloud infrastructure (YouTube Data API v3, Supabase PostgreSQL, Google Drive Cloud Storage, Telegram Bot API, and Discord Webhooks).

---

## 🛠️ Operational Tools Reference

### 1. `check_quotas_and_health`
* **Purpose:** Inspects real-time quota consumption and infrastructure connectivity.
* **Checks:**
  * **YouTube Data API v3:** Consumed units vs daily 10,000 unit ceiling (Upload: 1,600, Playlist: 50, Comment: 50). Status: `HEALTHY`, `WARNING`, or `EXHAUSTED`.
  * **Gemini API:** API Key connectivity and status.
  * **Supabase Cloud DB:** Connection status and row counts in `video_uploads` and `daily_summaries`.
  * **Google Drive Cloud Storage:** Canonical folder synchronization status.
  * **Local Archive & Disk:** Total archive size in MB and available free disk space in GB.
* **Schema:** [`check_quotas_and_health.json`](./check_quotas_and_health.json)

### 2. `check_content_deduplication`
* **Purpose:** Queries the 90-day archive to guarantee that news headlines or puzzle formulas are not recycled.
* **Parameters:**
  * `query` (str, required): Headline, topic, or puzzle problem to evaluate.
  * `lookback_days` (int, default: 90): Number of days in the past to inspect.
  * `content_type` (str, default: 'all'): `'news'`, `'teaser'`, or `'all'`.
* **Returns:** Jaccard similarity score, closest matching headline, historical date, and recommendation (`SAFE_TO_GENERATE` vs `DUPLICATE_DETECTED_REPHRASE`).
* **Schema:** [`check_content_deduplication.json`](./check_content_deduplication.json)

### 3. `get_render_diagnostics`
* **Purpose:** Inspects render outputs, slide asset counts, TTS audio alignment, and YouTube Shorts 60s compliance.
* **Parameters:**
  * `target_date` (str, optional): Target date in `YYYY-MM-DD` format (defaults to today).
  * `content_type` (str, default: 'daily'): `'daily'`, `'weekly'`, `'monthly'`, or `'brainteaser'`.
* **Returns:** Status of text file, slide image directory and count, `.mp4` video existence, file size in MB, and FFmpeg path resolution.
* **Schema:** [`get_render_diagnostics.json`](./get_render_diagnostics.json)

### 4. `dispatch_social_broadcast`
* **Purpose:** Previews or triggers multi-platform broadcast (Telegram and Discord) with native `.mp4` video attachments.
* **Parameters:**
  * `target_date` (str, optional): Target date in `YYYY-MM-DD` format.
  * `content_type` (str, default: 'daily'): `'daily'`, `'weekly'`, `'monthly'`, or `'brainteaser'`.
  * `dry_run` (bool, default: True): If True, previews HTML and Markdown captions without dispatching. If False, executes live API broadcast.
* **Returns:** Formatted Telegram HTML caption, Discord Markdown description, attached video path, and delivery status.
* **Schema:** [`dispatch_social_broadcast.json`](./dispatch_social_broadcast.json)

### 5. `trigger_pipeline_stage`
* **Purpose:** Autonomously executes a specific Pulse Vector pipeline stage (daily, weekly, monthly, brainteaser).
* **Parameters:**
  * `content_type` (str, default: 'daily'): `'daily'`, `'weekly'`, `'monthly'`, `'brainteaser'`, or `'all'`.
  * `target_date` (str, optional): Target date in `YYYY-MM-DD` format.
  * `stages` (list, optional): Granular stages (`['text', 'slides', 'video', 'youtube', 'sync']`).
  * `dry_run` (bool, default: False): Dry-run validation flag.
  * `force` (bool, default: False): Force regeneration of assets.
  * `no_tts` (bool, default: False): Disable voiceover synthesis.
* **Returns:** Execution status, duration in seconds, stdout summary, and return code.
* **Schema:** [`trigger_pipeline_stage.json`](./trigger_pipeline_stage.json)

### 6. `execute_autonomous_packup`
* **Purpose:** Executes the unified 6-phase master sign-off pipeline (/pulse_packup): diagnostics, asset hierarchy, 63-point test suite, storage cleanup, skills audit, and Git remote push.
* **Returns:** Phase statuses, overall PASS/FAIL result, and commit verification.
* **Schema:** [`execute_autonomous_packup.json`](./execute_autonomous_packup.json)

### 7. `auto_heal_environment`
* **Purpose:** Audits and self-heals workspace anomalies (purges temp render caches, verifies font assets, checks FFmpeg binaries).
* **Returns:** List of healed actions, detected issues, and health status.
* **Schema:** [`auto_heal_environment.json`](./auto_heal_environment.json)

### 8. `query_supabase_ledger`
* **Purpose:** Read-only inspection of Supabase cloud database records (`video_uploads`, `daily_summaries`, or `brain_teasers`).
* **Parameters:**
  * `table` (str, default: 'video_uploads'): Target table.
  * `limit` (int, default: 10): Row count limit (max 50).
  * `date_filter` (str, optional): Date filter substring.
* **Returns:** List of rows with sensitive tokens redacted.
* **Schema:** [`query_supabase_ledger.json`](./query_supabase_ledger.json)

### 9. `audit_token_and_quota_ledgers`
* **Purpose:** Audits current YouTube Data API quota units (10,000 daily budget ceiling) and recent token logs.
* **Returns:** Remaining YouTube quota units, status, and recent interaction turns.
* **Schema:** [`audit_token_and_quota_ledgers.json`](./audit_token_and_quota_ledgers.json)

---

## ⚙️ IDE Configuration

The server is registered in Antigravity IDE via `~/.gemini/config/mcp_config.json`:

```json
{
  "mcpServers": {
    "pulse-ops": {
      "command": "C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": [
        "e:\\hdd-data\\pulse-vector\\scripts\\run_pulse_mcp.py"
      ]
    }
  }
}
```

---

## 🧪 Testing

Execute the test suite to verify all MCP tools:
```bash
python scripts/test_pipeline.py
```
All 48 tests validate tool execution, edge cases, quota calculation, similarity matching, and broadcast dry-runs.
