# 🏛️ Pulse Vector — End-to-End System Design & Architecture

**Pulse Vector** is an enterprise-grade, fully autonomous content generation, video rendering, cloud archiving, and multi-platform distribution engine. It autonomously creates daily news intelligence shorts, weekly/monthly masterclasses, and interactive daily brain teasers formatted for vertical short-form platforms (YouTube Shorts, Discord, Telegram).

---

## 1. High-Level Architecture

The system operates across **6 decoupled layers**:
1. **Presentation & CLI Layer**: User interfaces, CLI arguments, and slash workflow triggers.
2. **Pipeline Orchestration Layer**: Pluggable stage execution engine with isolated state management.
3. **Core Processing & Media Engine**: AI content synthesis, category classification, dynamic graphics, neural TTS, procedural SFX, and video rendering.
4. **Distribution & Community Broadcast Layer**: YouTube Data API v3 publishing and real-time Discord/Telegram broadcasting.
5. **Data & Cloud Persistence Layer**: Local structured year/month archive and remote Supabase PostgreSQL metadata logging.
6. **Operations, Health & Diagnostics Layer**: System diagnostic monitors, automated test suites, storage optimizers, and unified packup engine.

```mermaid
graph TD
    CLI["CLI / Slash Workflows<br>(/packup, /pulse_daily, /pulse_test)"] --> Engine["Pipeline Engine<br>(src/core/pipeline_engine.py)"]
    
    subgraph "Orchestration & Stage Execution"
        Engine --> S1["Stage: Text (GenAI & Fallbacks)"]
        Engine --> S2["Stage: Slides (PIL & Categories)"]
        Engine --> S3["Stage: Voiceover (Edge-TTS)"]
        Engine --> S4["Stage: Video (FFmpeg, SFX & Karaoke)"]
        Engine --> S5["Stage: YouTube & Community Broadcast"]
        Engine --> S6["Stage: Cloud Sync (Supabase & Git)"]
    end

    subgraph "External Cloud Services & APIs"
        S1 --> Gemini["Gemini 2.5 Flash<br>+ Gemma / Groq Fallbacks"]
        S5 --> YT["YouTube Data API v3<br>(OAuth2 & Resumable Upload)"]
        S5 --> Discord["Discord Webhook<br>(Rich Embeds & Cards)"]
        S5 --> Telegram["Telegram Bot API<br>(HTML & Photo Dispatch)"]
        S6 --> Supabase["Supabase Cloud DB<br>(PostgreSQL pipeline_runs)"]
        S6 --> GitHub["GitHub Remote CI/CD<br>(git push origin main)"]
    end
```

---

## 2. Component Architecture & Separation of Concerns

```
pulse-vector/
├── src/
│   ├── pipeline.py                 # Primary CLI entrypoint (daily, weekly, monthly)
│   ├── brainteaser_pipeline.py     # Standalone Brain Teaser generation & publishing engine
│   ├── daily_pipeline.py           # Daily Current Affairs pipeline runner
│   ├── weekly_pipeline.py          # Weekly Masterclass pipeline runner
│   ├── monthly_pipeline.py         # Monthly Masterclass pipeline runner
│   └── core/
│       ├── config.py               # Central environment variables, paths & constants
│       ├── genai_utils.py          # Multi-model LLM generation & fallback routing
│       ├── content_parser.py       # Pure logic parsing, category classification, regex sanitization
│       ├── image_utils.py          # PIL mobile card layout, typography & category badges
│       ├── video_utils.py          # Video compositing, transitions, procedural SFX, karaoke overlay
│       ├── tts_utils.py            # Neural Edge-TTS voiceover synthesis & speech alignment checks
│       ├── youtube_utils.py        # YouTube OAuth authentication, chunked uploads, comment posting
│       ├── database_utils.py       # Supabase PostgreSQL metadata logging & archive sync
│       ├── broadcast_utils.py      # Multi-platform Telegram Bot & Discord Webhook dispatcher
│       └── pipeline_engine.py      # Decoupled stage orchestrator (text, slides, video, upload)
├── scripts/
│   ├── monitor_health.py           # System diagnostic tool (APIs, FFmpeg, OAuth, Supabase)
│   ├── test_pipeline.py            # Offline 20-point automated unit test suite & dry-runs
│   ├── cleanup_workspace.py        # Workspace storage analyzer & safe temporary files purger
│   └── packup_pipeline.py          # Unified master sign-off engine orchestrating all workflows
├── .agent/
│   ├── workflows/                  # Slash workflows (/packup, /pulse_daily, /pulse_clean, etc.)
│   └── skills/                     # Domain skills (content-gen, media-rendering, youtube-dist, etc.)
└── pulse_archive/                  # Partitioned historical storage (YYYY/Month/Type/)
```

---

## 3. Detailed Data Flow Pipelines

### A. Current Affairs Pipeline (Daily, Weekly, Monthly)

```mermaid
sequenceDiagram
    autonumber
    participant CLI as CLI / Workflow
    participant Engine as PipelineEngine
    participant GenAI as Gemini / Groq API
    participant Parser as ContentParser
    participant ImageGen as ImageUtils (PIL)
    participant TTS as Edge-TTS Engine
    participant VideoGen as VideoUtils (FFmpeg)
    participant Dist as YouTube & Broadcast
    participant DB as Supabase DB

    CLI->>Engine: run_pipeline(content_type, target_date)
    Engine->>GenAI: Query headlines with grounding / search
    GenAI-->>Engine: Raw Markdown report
    Engine->>Parser: parse_news_content(raw_text)
    Parser->>Parser: Strip metadata & classify_news_category()
    Parser-->>Engine: Structured NewsPayload (points, sources, categories)
    
    Engine->>ImageGen: create_slide_image_file() per 5 headlines
    ImageGen-->>Engine: 1080x1920 Glassmorphic slide PNGs with category badges
    
    Engine->>TTS: synthesize_speech_segments() (Voice: Christopher, Rate: +35%)
    TTS-->>Engine: Timed MP3 segments & speech verification
    
    Engine->>VideoGen: compile_video_with_audio_and_transitions()
    VideoGen-->>Engine: 60-second high-retention vertical MP4
    
    Engine->>Dist: upload_video_to_youtube() & add_to_playlist()
    Dist-->>Engine: Video ID & Published URL
    
    Engine->>Dist: broadcast_daily_content(Telegram & Discord)
    Dist-->>Engine: Broadcast status confirmations
    
    Engine->>DB: run_database_upload(run_metadata)
    DB-->>Engine: Run logged in Supabase
```

---

### B. Daily Brain Teasers Pipeline (Shorts & Community Engagement)

```mermaid
sequenceDiagram
    autonumber
    participant BT as BrainTeaserPipeline
    participant GenAI as Gemini API
    participant PIL as Card & Outro Renderer
    participant SFX as Procedural Audio Engine
    participant TTS as Christopher Voiceover
    participant Video as Video Compositor
    participant YT as YouTube API
    participant Social as Discord & Telegram

    BT->>GenAI: build_brainteaser_prompt(weekday archetype)
    Note over BT,GenAI: 7 Archetypes: BODMAS, Grid, Cipher, Sequence, Lateral, etc.
    GenAI-->>BT: Structured puzzle text & answer
    
    BT->>PIL: Render 656x656 high-contrast styled puzzle card
    BT->>TTS: Synthesize intro hook ("Daily Brain Teaser! Can you solve...")
    BT->>Video: compute_word_timings(character-proportional)
    
    loop 120 Frames (12.0s @ 10 FPS)
        alt 0.0s to 4.5s (Voiceover active)
            Video->>Video: Render dynamic animated Karaoke Subtitle capsule
        else 4.5s to 8.0s (Thinking countdown)
            Video->>Video: Render cyan countdown progress ring & seconds left
        else 8.0s to 12.0s (Outro slide)
            Video->>Video: Render glassmorphic card with animated swinging golden bell
        end
    end
    
    BT->>SFX: generate_countdown_sfx() (Woodblock ticks + resonant chime)
    BT->>Video: merge_brainteaser_audio() (Voiceover + SFX + ducked BGM)
    Video-->>BT: Final 12.0s Short MP4
    
    BT->>YT: upload_video_to_youtube()
    YT-->>BT: Published Video ID
    
    BT->>YT: format_teaser_challenge_comment() -> challenge-comment-[date].txt
    BT->>YT: format_solution_reveal_comment() -> solution-reveal-[yesterday].txt
    BT->>Social: broadcast_daily_content() to Discord & Telegram
```

---

## 4. Media & Visual Rendering Subsystem

### 1. Canvas Dimensions & Aspect Ratio
- **Resolution**: `1080 × 1920` pixels (Vertical 9:16 aspect ratio optimized for mobile YouTube Shorts).
- **Background Glow**: Multi-stop radial gradients with Gaussian blurred colour nodes (Cyan `#06b6d4`, Violet `#8b5cf6`, Magenta `#d946ef`, radius: 200).
- **Glassmorphism Spec**: Rounded rectangles with semi-transparent dark fills (`rgba(15, 23, 42, 0.65)`), crisp 1px borders (`rgba(255, 255, 255, 0.14)`), and subtle drop shadows.

### 2. Thematic Category Classifier (`content_parser.py`)
Automatically detects news topic and assigns distinctive editorial colour palettes:

| Category | Accent Color | Hex | Micro-Pill Tag |
| :--- | :--- | :--- | :---: |
| **DEFENCE** | Crimson / Coral | `#f43f5e` | `[DEFENCE]` |
| **ECONOMY** | Amber / Gold | `#f59e0b` | `[ECONOMY]` |
| **TECH & AI** | Electric Cyan | `#06b6d4` | `[TECH & AI]` |
| **GEOPOLITICS** | Deep Violet | `#8b5cf6` | `[GEOPOLITICS]` |
| **ENVIRONMENT** | Emerald Green | `#10b981` | `[ENVIRONMENT]` |
| **NATIONAL** | Royal Blue | `#3b82f6` | `[NATIONAL]` |
| **GLOBAL** | Slate Gray | `#64748b` | `[GLOBAL]` |

### 3. Dynamic Karaoke Subtitle Engine (`video_utils.py`)
- **Timing**: `compute_word_timings()` assigns sub-second character-weighted durations to every spoken word.
- **Visual Grouping**: Words grouped into 3–4 word reading capsules.
- **Active Highlighting**: Current word illuminates in vibrant **electric gold (`#facc15`)**, accompanied by a subtle breathing capsule outline (`rgba(250, 204, 21, 0.4)`).
- **Safety Margins**: Centered vertically at $Y = 1350$, leaving 26px clear margin below the puzzle card and 29px clear margin above the countdown ring.

### 4. Multi-Track Audio Engine (`video_utils.py`)
Video audio is multiplexed across 3 concurrent stereo audio streams:
- **Track 1 (Voiceover)**: Neural TTS (`en-US-ChristopherNeural`) with high-clarity gain.
- **Track 2 (Procedural SFX)**: Mathematically synthesized woodblock clock ticks (800 Hz to 400 Hz exponentially decaying sines) + 523.25 Hz resonant chime.
- **Track 3 (Background Music)**: Ducked ambient royalty-free soundtrack (volume reduced by 75% during voiceover periods).

---

## 5. Multi-Platform Community Distribution Subsystem

### 1. YouTube Distribution
- **Authentication**: OAuth 2.0 with automatic token refresh (`credentials/token.json`).
- **Resumable Chunked Upload**: Resilient against network drops (5MB chunk size).
- **Playlist Routing**: Auto-routes videos into dedicated playlists (`DailyCurrentAffairs`, `WeeklyMasterclass`, `MonthlyMasterclass`, `BrainTeasers`).
- **Safety Quota Management**: Strict daily quota accounting tracked in `Research/youtube_quota_log.md`.

### 2. Discord Webhook Broadcast
- **Protocol**: HTTP POST to `DISCORD_WEBHOOK_URL`.
- **Payload**: Rich Discord Embed with category colour sidebars, puzzle title, formatted option list, and direct YouTube video button.
- **Media Attachment**: High-resolution PNG slide automatically uploaded as a multipart attachment.

### 3. Telegram Bot API Broadcast
- **Protocol**: HTTP POST via `https://api.telegram.org/bot<TOKEN>/sendPhoto`.
- **Formatting**: Rich HTML captions with bold headers, italics, bullet lists, and clickable hyperlinks.
- **Fallback**: Graceful fallback to `sendMessage` if image upload is unavailable.

---

## 6. Fault Tolerance & Graceful Degradation Strategy

| Failure Scenario | Built-in Mitigation & Fallback Strategy |
| :--- | :--- |
| **Gemini 2.5 Rate Limit / Outage** | Automatically falls back to secondary models: `gemini-2.0-flash` $\to$ `gemini-1.5-flash` $\to$ Groq Llama 3.3. |
| **No Internet for Edge-TTS** | Pipeline proceeds with silent visual slides or background music only via `--no-tts` flag. |
| **Missing Discord / Telegram Keys** | `broadcast_daily_content()` catches `None` credentials, logs an informational skip, and returns `False` without crashing. |
| **Audio Track Missing** | Merges video cleanly with procedural SFX only, bypassing background music. |
| **YouTube Token Expired** | Uses OAuth refresh token to renew session silently without user intervention. |

---

## 7. Quality Assurance, Testing & Operations

### 1. Offline Automated Test Suite (`scripts/test_pipeline.py`)
- **Coverage**: 20 modular unit tests spanning regex markdown strippers, news point extractors, BODMAS/Grid/Cipher parsers, slide layout renderers, karaoke subtitle overlays, procedural audio generators, and pipeline dry-runs.
- **Execution Speed**: 20 tests run in under **2.0 seconds** completely offline without burning API quota.

### 2. Unified Master Packup Engine (`scripts/packup_pipeline.py` & `/packup`)
A single slash workflow `/packup` orchestrates 6 sequential phases:
1. `monitor_health.py` (Diagnostics for APIs, FFmpeg, Supabase, OAuth).
2. Asset & Structure Audit (Fonts, 15 audio tracks, archive hierarchy).
3. Test Suite (20 unit tests & dry-runs).
4. Storage Optimizer (Purges temp frames, dangling wavs, and bytecode cache).
5. Domain Skills Audit (Verifies all 6 skills in `.agent/skills/`).
6. Remote Git Synchronization (`git push origin main`).
