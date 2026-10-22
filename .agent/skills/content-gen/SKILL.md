---
name: content-gen
description: Domain skill for Gemini API integration, prompt templates, Current Affairs summaries, and Brain Teaser generation.
---

# Content Generation & AI Domain Skill

## Scope & Target Files
- `src/*_pipeline.py` (Daily, Weekly, Monthly, Brain Teaser pipelines)
- `src/core/genai_utils.py`

## Instructions & Core Operations
1. **Gemini API Model Invocation**:
   - Use `genai_utils.py` helpers to initialize Gemini clients.
   - Use temperature setting `0.2` - `0.4` for structured factual Current Affairs to minimize hallucinations.
   - Use temperature `0.7` for creative Brain Teaser puzzle generation.
2. **Current Affairs Rules**:
   - Daily summaries: 15 structured factual points.
   - Weekly summaries (Sundays): 30 masterclass points.
   - Monthly summaries (End of month): 50 comprehensive points.
3. **Brain Teasers**:
   - Supported categories (13 total): `bodmas`, `cipher`, `grid`, `trap`, `sequence`, `oddone`, `paradox`, `detective`, `relations`, `weighing`, `spatial`, `matchstick`, `age_speed`.
   - Dynamic Random Selection: Default to dynamic random selection across all 13 categories to ensure variety, high retention, and surprise factor.
   - Quality Standards: Every puzzle must have a single unequivocal answer, 4 plausible MCQ options (a., b., c., d.), 10-second readability, and a step-by-step logic explanation.


## Domain Constraints
- Never hardcode API keys; retrieve strictly from `GEMINI_API_KEY` environment variable.
- Enforce strict JSON / Markdown structured output schemas to prevent parser failures downstream.
- Catch API rate limits (429) or unavailability gracefully with fallback retry logic.

## Verification Checklist
- [ ] Verify `GEMINI_API_KEY` is active in `.env`.
- [ ] Execute `python src/pipeline.py --list-models` to confirm API connectivity.
- [ ] Validate output format of generated content file matches schema requirements.
