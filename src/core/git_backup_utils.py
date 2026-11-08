import os
import shutil
import logging
import subprocess
from .config import ARCHIVE_DIR, BACKUP_DIR

def run_git_operations(commit_msg="Auto-update: Pulse Vector Pipeline Run"):
    print("\n🚀 Starting Git Operations...")
    logging.info("Starting git operations...")
    project_root = ARCHIVE_DIR.parent
    
    try:
        # Pull remote updates first with autostash and theirs conflict strategy
        subprocess.run(["git", "pull", "--rebase", "--autostash", "-X", "theirs", "origin", "main"], cwd=project_root, check=False)
        
        subprocess.run(["git", "add", "."], cwd=project_root, check=True)
        print("✅ Git Add completed.")
        
        status = subprocess.run(["git", "status", "--porcelain"], cwd=project_root, capture_output=True, text=True)
        if not status.stdout.strip():
            print("No changes to commit.")
            logging.info("No changes to commit.")
            return
            
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=project_root, check=True)
        print(f"✅ Git Commit completed: '{commit_msg}'")
        
        # Pull again to ensure rebase onto any concurrent commits using theirs strategy
        pull_res = subprocess.run(["git", "pull", "--rebase", "-X", "theirs", "origin", "main"], cwd=project_root, capture_output=True, text=True)
        if pull_res.returncode != 0:
            logging.warning("Rebase conflict detected; falling back to merge strategy...")
            subprocess.run(["git", "rebase", "--abort"], cwd=project_root, check=False)
            subprocess.run(["git", "pull", "--no-rebase", "-X", "theirs", "origin", "main", "--no-edit"], cwd=project_root, check=False)

        logging.info("Git operations completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        logging.error(f"Git operation failed: {e}")

def run_backup_operations():
    print("\n🚀 Starting External Backup...")
    logging.info("Starting external backup...")
    if not BACKUP_DIR:
        print("ℹ️ External backup skipped (PULSE_BACKUP_DIR not set or G: drive not mounted).")
        logging.info("External backup skipped (no BACKUP_DIR).")
        return
    try:
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            
        for item in os.listdir(ARCHIVE_DIR):
            s = os.path.join(ARCHIVE_DIR, item)
            d = os.path.join(BACKUP_DIR, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
                
        print(f"✅ Backup completed successfully to: {BACKUP_DIR}")
        logging.info(f"Backup completed to {BACKUP_DIR}")
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        logging.error(f"Backup failed: {e}")

