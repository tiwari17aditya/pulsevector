"""
Pulse Vector — Safe Channel Branding Branch Switcher & Runner
Orchestrates seamless context switching between feature/development branches and the branding branch:
  1. Detects and stores the current branch (e.g., v2.9.0-dev, v2.4.2-dev).
  2. Safely stashes any dirty working tree changes on the dev branch.
  3. Checks out 'channel-branding-update' and pulls the latest remote state.
  4. Executes the requested branding action (--review, --apply, or --interactive).
  5. If changes were applied, commits and pushes to origin/channel-branding-update.
  6. Switches back to the original development branch.
  7. Pops any stashed changes to leave the developer workspace completely undisturbed.
"""

import sys
import os
import subprocess
import argparse
import pathlib

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent

def run_git(args: list, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        check=check
    )

def get_current_branch() -> str:
    res = run_git(["branch", "--show-current"])
    return res.stdout.strip()

def has_dirty_working_tree() -> bool:
    res = run_git(["status", "--porcelain"])
    return bool(res.stdout.strip())

def main():
    parser = argparse.ArgumentParser(description="Branding Branch Switcher & Orchestrator")
    parser.add_argument("--review", action="store_true", help="Review branding without applying live changes")
    parser.add_argument("--apply", action="store_true", help="Apply approved changes to YouTube live")
    parser.add_argument("--upload-banner", action="store_true", help="Also upload master banner")
    parser.add_argument("--target-branch", default="channel-branding-update", help="Branding branch name")
    parser.add_argument("--stay", action="store_true", help="Stay on branding branch instead of switching back")
    args = parser.parse_args()

    orig_branch = get_current_branch()
    target_branch = args.target_branch
    stashed = False

    print("\n" + "=" * 68)
    print("  🔄 PULSE VECTOR — BRANDING BRANCH SWITCHER & ORCHESTRATOR")
    print("=" * 68)
    print(f"Current Active Branch: {orig_branch}")
    print(f"Branding Target Branch: {target_branch}")

    try:
        # Step 1: Stash if dirty
        if orig_branch != target_branch:
            if has_dirty_working_tree():
                print("\n📦 Workspace has uncommitted changes. Stashing before branch switch...")
                run_git(["stash", "save", "--include-untracked", "branding-switch-autostash"])
                stashed = True
            else:
                print("✅ Working tree is clean.")

            # Step 2: Checkout branding branch
            print(f"\n🔀 Switching to '{target_branch}'...")
            run_git(["checkout", target_branch])
            print(f"⬇️ Pulling latest changes from origin/{target_branch}...")
            run_git(["pull", "origin", target_branch], check=False)

        # Step 3: Run branding lifecycle
        lifecycle_script = ROOT_DIR / "channel_branding" / "branding_lifecycle.py"
        if not lifecycle_script.exists():
            raise FileNotFoundError(f"Branding lifecycle script not found: {lifecycle_script}")

        cmd = [sys.executable, str(lifecycle_script)]
        if args.apply:
            cmd.append("--apply")
            if args.upload_banner:
                cmd.append("--upload-banner")
            cmd.append("--commit-push")
        else:
            cmd.append("--review")

        print(f"\n▶ Running: {' '.join(cmd)}...")
        sub_res = subprocess.run(cmd, cwd=str(ROOT_DIR), text=True, encoding='utf-8')
        if sub_res.returncode != 0:
            print(f"⚠️ Lifecycle command exited with code {sub_res.returncode}")

    finally:
        # Step 4: Switch back to original branch
        if not args.stay and orig_branch != target_branch:
            print(f"\n🔙 Switching back to original branch: {orig_branch}...")
            run_git(["checkout", orig_branch])
            if stashed:
                print("📦 Restoring previously stashed working tree changes...")
                run_git(["stash", "pop"], check=False)
            current_after = get_current_branch()
            print(f"✅ Successfully returned to development branch: {current_after}")
        elif args.stay:
            print(f"ℹ️ Remaining on branch '{target_branch}' (--stay flag passed).")

    print("\n" + "=" * 68)
    print("  🎉 BRANDING CYCLE OPERATION COMPLETE")
    print("=" * 68)

if __name__ == "__main__":
    main()
