---
description: Generate Daily Current Affairs or Brain Teasers for Pulse Vector
---

# Pulse Vector Daily Content Generator

This workflow automates the creation of content based on the `pulse_prompts.md` definitions.

## Steps

1.  **Read Prompts**: Read the `.agent/pulse_prompts.md` file to load the specific persona and formatting rules.
2.  **Identify Date**: Determine the current date (and check if it is Sunday or Month-End for formatting logic).
3.  **Search Information**:
    *   If generating Current Affairs: Search for "Current Affairs [Date]", "Top News Stories [Date]", "International News [Date]".
    *   If generating Brain Teaser: Create a novel sequence puzzle (logic based, no search needed usually, or search for inspiration).
4.  **Generate Content**:
    *   Use the *Current Affairs Prompt* to format the news headlines.
    *   Use the *Brain Teaser Prompt* to create the puzzle text.
5.  **Generate Assets**:
    *   If Brain Teaser: Use `generate_image` to create the visual puzzle.
6. **Archive**:
    *   **Structure**: `pulse_archive/[Year]/[FullMonthName]/...`
    *   **Current Affairs**:
        *   Daily: `Daily/daily-[d][mon]-[yyyy]_formatted.txt` (e.g., `daily-2feb-2026_formatted.txt`)
        *   Weekly: `Weekly/weekly-[dd]-[mon]-[yyyy].txt`
        *   Monthly: `Monthly/monthly-[mon]-[yyyy].txt`
    *   **Brain Teasers**:
        *   Text: `Brain_Teasers/brainteaser-[d][mon][yy].txt` (e.g., `brainteaser-2feb26.txt`)
        *   Image: `Brain_Teasers/brainteaser-[d][mon][yy].png`

## Usage
Run this workflow and specify if you want "CA" (Current Affairs), "BT" (Brain Teaser), or "Both".
