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
