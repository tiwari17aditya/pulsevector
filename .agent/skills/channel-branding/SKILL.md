---
name: channel-branding
description: Domain skill for YouTube channel branding, visual identity, banner/icon generation, Home Tab shelves optimization, and version ledger tracking on the dedicated channel-branding-update branch.
---

# Channel Branding Domain Skill

## Scope & Target Files
- `channel_branding/branding_lifecycle.py`
- `channel_branding/switch_and_update_branding.py`
- `channel_branding/update_youtube_channel.py`
- `channel_branding/setup_hometab_sections.py`
- `channel_branding/archive_branding_version.py`
- `channel_branding/channel_details.json`
- `channel_branding/branding_ledger.json`
- `channel_branding/branding_ledger.md`
- `channel_branding/assets/*`
- `channel_branding/history/*`

## Instructions & Core Operations

1. **Branch Segregation**:
   - All branding operations MUST run strictly on `channel-branding-update`.
   - Never develop or test branding changes directly on `main` or `v<version>-dev`.
   - Always return to the active development branch upon completion.

2. **Visual Standards & Safe Zones**:
   - Master Banner: $2560 \times 1440$ px, with critical content centered within $1546 \times 423$ px desktop/mobile safe area.
   - Profile Icon: $1024 \times 1024$ px master and $800 \times 800$ px production export.
   - Design: Photorealistic, cinematic, sharp, high-contrast, representing all core pillars (*Current Affairs*, *Brain Teasers*, *Mahabharat Animated*, *Last Day on Earth Survival*).

3. **Home Tab Architecture**:
   - Up to 7 optimized shelves:
     1. Daily Current Affairs (Oct - Dec 2026)
     2. Last Day on Earth: Survival Series (105 episodes)
     3. Daily Brain Teasers — 2026 (97 episodes)
     4. Mahabharat: The Epic Battle of Dharma (70 episodes)
     5. Weekly Current Affairs Masterclasses (23 episodes)
     6. Latest Uploads (`recentuploads`)
     7. All Playlists Directory (`allplaylists`)
   - Zero tolerance for broken `channelsectiontypeundefined` shelves.

4. **Review & Confirmation Standard**:
   - Always display comparison dashboard (`--review`) before modifying live YouTube settings.
   - Require explicit user confirmation before executing `--apply`.

5. **Ledger & History Archive**:
   - Every live deployment must snapshot assets into `channel_branding/history/v<version>_<date>_<codename>/`.
   - Maintain `branding_ledger.json` and `branding_ledger.md` with active CDN URLs.

6. **Automated Runner**:
   - Execute `python channel_branding/switch_and_update_branding.py --review` (or `--apply`).
