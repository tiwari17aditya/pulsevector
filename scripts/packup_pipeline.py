"""
Pulse Vector - Unified Packup & Sign-Off Engine
Orchestrates all slash workflows and audits all domain skills:
1. /pulse_monitor   - Cloud APIs, FFmpeg, Supabase, OAuth, TTS health diagnostics
2. /pulse_structure - Fonts, audio library, archive directory hierarchy verification
3. /pulse_test      - 20-point automated test suite & pipeline stage dry-runs
4. /pulse_clean     - Safe purge of temporary render frames, dangling audio, and scratch files
5. Domain Skills    - Integrity audit across all 6 skills in .agent/skills/
6. Git Automation   - Remote synchronization (git push origin main) and session sign-off
"""

import os
import sys
import subprocess
import pathlib
import datetime
import shutil

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent

def print_header(title: str):
    print("\n" + "=" * 62)
    print(f"  🚀 PULSE VECTOR PACKUP: {title.upper()}")
    print("=" * 62)

def run_command_logged(cmd: list, desc: str) -> bool:
    print(f"\n▶ Running: {desc}...")
    try:
        res = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, encoding='utf-8', errors='replace')
        if res.stdout:
            print(res.stdout.strip())
        if res.returncode != 0:
            if res.stderr:
                print(f"❌ Error Output:\n{res.stderr.strip()}")
            return False
        return True
    except Exception as e:
        print(f"❌ Execution exception: {e}")
        return False

def audit_domain_skills() -> bool:
    print("\n▶ Auditing Domain Skills in .agent/skills/...")
    skills_dir = ROOT_DIR / ".agent" / "skills"
    if not skills_dir.exists():
        print("❌ .agent/skills/ directory not found.")
        return False
        
    expected_skills = [
        "content-gen",
        "media-rendering",
        "youtube-dist",
        "cloud-db",
        "pipeline-git",
        "clean-optimizer"
    ]
    
    all_ok = True
    for skill_name in expected_skills:
        skill_path = skills_dir / skill_name / "SKILL.md"
        if not skill_path.exists():
            print(f"  ❌ Missing skill: {skill_name} ({skill_path})")
            all_ok = False
        else:
            size = skill_path.stat().st_size
            print(f"  ✅ [PASS] Skill '{skill_name}' verified ({size} bytes)")
            
    return all_ok

def audit_structure() -> bool:
    print("\n▶ Auditing Workspace Structure & Asset Hierarchy (/pulse_structure)...")
    fonts_dir = ROOT_DIR / "fonts"
    audio_dir = ROOT_DIR / "samples" / "Audio"
    archive_dir = ROOT_DIR / "pulse_archive"
    
    all_ok = True
    
    # 1. Fonts
    required_fonts = ["Roboto-Regular.ttf", "Roboto-Bold.ttf"]
    for f in required_fonts:
        fpath = fonts_dir / f
        if not fpath.exists():
            print(f"  ❌ Missing required font: {f}")
            all_ok = False
        else:
            print(f"  ✅ [PASS] Font: {f} ({fpath.stat().st_size} bytes)")
            
    # 2. Audio Library
    if audio_dir.exists():
        tracks = list(audio_dir.glob("*.mp3"))
        print(f"  ✅ [PASS] Audio Library: {len(tracks)} royalty-free tracks found")
    else:
        print("  ⚠️ Audio directory missing or empty")
        
    # 3. Pulse Archive
    if archive_dir.exists():
        arch_files = list(archive_dir.glob("**/*"))
        arch_size = sum(f.stat().st_size for f in arch_files if f.is_file())
        print(f"  ✅ [PASS] Archive Health: {arch_size / (1024*1024):.2f} MB across {len(arch_files)} objects")
    else:
        print("  ❌ Archive root not found")
        all_ok = False
        
    return all_ok

def main():
    print_header("Unified Master Execution")
    print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Workspace: {ROOT_DIR}")
    
    results = {}
    
    # Phase 1: /pulse_monitor (System Diagnostics)
    results["monitor"] = run_command_logged(
        [sys.executable, str(ROOT_DIR / "scripts" / "monitor_health.py")],
        "System Health Diagnostics (/pulse_monitor)"
    )
    
    # Phase 2: /pulse_structure (Structure & Asset Audit)
    results["structure"] = audit_structure()
    
    # Phase 3: /pulse_test (Automated Test Suite & Dry-Runs)
    results["tests"] = run_command_logged(
        [sys.executable, str(ROOT_DIR / "scripts" / "test_pipeline.py")],
        "20-Point Test Suite & Dry-Runs (/pulse_test)"
    )
    
    # Phase 4: /pulse_clean (Workspace Storage & Artifact Purge)
    results["cleanup"] = run_command_logged(
        [sys.executable, str(ROOT_DIR / "scripts" / "cleanup_workspace.py"), "--clean"],
        "Workspace Storage & Temp File Cleaner (/pulse_clean)"
    )
    
    # Phase 5: Domain Skills Integrity Audit
    results["skills"] = audit_domain_skills()
    
    # Phase 6: Remote Git Synchronization
    print("\n▶ Checking Git Repository Status...")
    status_res = subprocess.run(["git", "status", "-s"], cwd=str(ROOT_DIR), capture_output=True, text=True)
    pending_changes = bool(status_res.stdout.strip())
    
    if pending_changes:
        print("  ⚠️ Uncommitted changes detected. Auto-staging and committing...")
        subprocess.run(["git", "add", "."], cwd=str(ROOT_DIR))
        subprocess.run(["git", "commit", "-m", "chore(packup): automated sign-off and session synchronization"], cwd=str(ROOT_DIR))

    # Detect current active branch
    branch_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(ROOT_DIR), capture_output=True, text=True)
    current_branch = branch_res.stdout.strip() or "main"

    # Pull with rebase to ensure local is up-to-date with remote commits
    print(f"  🔄 Rebase-syncing with origin/{current_branch}...")
    subprocess.run(["git", "pull", "--rebase", "origin", current_branch], cwd=str(ROOT_DIR))
    push_res = subprocess.run(["git", "push", "origin", current_branch], cwd=str(ROOT_DIR), capture_output=True, text=True)
    if push_res.returncode == 0:
        print(f"  ✅ Successfully pushed all changes to origin/{current_branch}.")
        results["git_push"] = True
    else:
        print(f"  ❌ Git push warning: {push_res.stderr.strip()}")
        results["git_push"] = False

    # Final Scorecard
    print_header("Final Sign-Off Scorecard")
    all_passed = True
    for phase, passed in results.items():
        icon = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {icon} - Phase: {phase}")
        if not passed:
            all_passed = False
            
    if all_passed:
        print("\n🎉 ALL WORKFLOWS, SKILLS & TESTS PASSED! Safe to sign off.")
        sys.exit(0)
    else:
        print("\n⚠️ Some checks failed. Review output above before final sign-off.")
        sys.exit(1)

if __name__ == "__main__":
    main()
