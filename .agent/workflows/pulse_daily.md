---
description: Generate Daily Current Affairs or Brain Teasers for Pulse Vector
---

# Pulse Vector Daily Content Generator

This workflow automates the creation of content and YouTube upload operations based on the **Pulse Vector** channel strategy.

## 🎯 Channel Identity & Positioning
* **Channel Name**: Pulse Vector
* **Channel Tagline**: "Where Ancient History meets Modern Knowledge"
* **Channel Bio / About**: "Pulse Vector — Where Ancient History meets Modern Knowledge. Master the epic history of the Mahabharat through high-quality 9:16 animated shorts, and stay ahead with concise Daily, Weekly & Monthly Current Affairs for exams and general awareness."

---

## Steps

1.  **Read Prompts**: Read the prompt definitions to load persona and formatting rules.
2.  **Identify Date**: Determine current date (and check if Sunday or Month-End for Weekly/Monthly summaries).
3.  **Search Information**:
    *   If Current Affairs: Search for "Current Affairs [Date]", "Top News Stories [Date]", "International News [Date]".
    *   If Brain Teaser: Create a novel sequence puzzle.
4.  **Generate Content**:
    *   Current Affairs: Format news headlines into structured daily/weekly/monthly points.
    *   Brain Teaser: Generate puzzle text.
5.  **Generate Assets & Videos**:
    *   Render glassmorphism slides and compile MP4 videos with background audio.
6.  **YouTube Upload & Metadata Integration**:
    *   **Category**: Education (Category ID `27`).
    *   **Related Video Setting**:
        *   Daily Shorts: Link to latest "Weekly Current Affairs Masterclass" (or previous Daily episode).
        *   Weekly / Monthly: Link to Channel Homepage & Current Affairs Playlist.
    *   **Pinned Comment**: Immediately post & pin:
        > 🧠 Master your exam prep with daily 60-second Current Affairs updates! 
        > 📚 Watch our full Weekly Masterclass: [Link]
        > 🔔 Subscribe to Pulse Vector & turn on notifications so you never miss a day!
        > Which question should we feature in tomorrow's quiz? Drop it below! 👇
    *   **Track Upload**: Update `Research/youtube_upload_details.md` with Video Title, Category, Related Video Setting, and Pinned Comment status.
7.  **Community Tab Engagement Schedule**:
    *   **8:00 AM IST**: Daily Current Affairs Quiz Poll (4 options for UPSC/SSC/Govt exams).
    *   **1:00 PM IST**: Daily Top 5 Headlines Summary Infographic card.
8. **Archive & Git Commit**:
    *   Archive generated files under `pulse_archive/[Year]/[FullMonthName]/...`.
    *   Commit all tracked files to Git after every compilation/render.

---

## 🤖 Critical Agent Guidelines (MANDATORY)

Every AI assistant/agent interacting with this repository MUST strictly follow these rules:

1. **Git Commit/Push Restrictions**: Keep tracked metadata files up-to-date and commit changes to Git after every compilation/render.
2. **Token Usage Reporting**: In every final response of a turn, provide an estimate of the input and output tokens used during the turn (estimate: ~4 characters per token), and automatically append a new log entry for the session/turn to the tracker file [developer_token_usage.md](file:///d:/New%20folder/pulse-vector/Research/developer_token_usage.md).
3. **YouTube Quota Tracking**: Keep track of the remaining YouTube API upload quota and upload limit in every YouTube-related turn:
   * Daily query quota: 10,000 units.
   * Daily video upload limit: 100 videos.
   * Track the number of uploads made today and report the remaining uploads and query quota, and log the everyday count usage and quota left after everyday push to YouTube in the tracker file [youtube_quota_log.md](file:///d:/New%20folder/pulse-vector/Research/youtube_quota_log.md).


