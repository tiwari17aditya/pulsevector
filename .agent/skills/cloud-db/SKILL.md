---
name: cloud-db
description: Domain skill for Supabase PostgreSQL database metadata logging, Cloud Storage bucket uploads, and archive migrations.
---

# Supabase Cloud & DB Domain Skill

## Scope & Target Files
- `src/core/database_utils.py`
- `scripts/setup_supabase.py`
- `scripts/migrate_archive_to_supabase.py`

## Instructions & Core Operations
1. **Cloud Storage Bucket Management**:
   - Target bucket: `pulse-vector-media`.
   - Store compiled MP4 videos and full-resolution slide graphics to bypass local storage and GitHub repo size boundaries.
   - Maintain folder path symmetry: `pulse-vector-media/[Year]/[Month]/[Category]/[filename]`.
2. **PostgreSQL Database Logging**:
   - Record pipeline execution runs, file paths, Supabase public URLs, and execution metrics into Supabase database tables via `database_utils.py`.

## Domain Constraints
- Read connection strings strictly from environment variables `SUPABASE_URL` and `SUPABASE_KEY`.
- Implement retry wrappers for bucket uploads to withstand transient network drops.

## Verification Checklist
- [ ] Confirm `SUPABASE_URL` and `SUPABASE_KEY` exist in `.env`.
- [ ] Execute `python scripts/setup_supabase.py` to verify bucket and table access.
- [ ] Verify generated media file public URL accessible after bucket upload.
