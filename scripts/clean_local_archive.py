import os
import sys
import shutil
import stat
import time

def remove_readonly(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        print(f"Error removing {path}: {e}")

def main():
    archive_dir = "pulse_archive"
    if not os.path.exists(archive_dir):
        print(f"Directory {archive_dir} does not exist.")
        return

    items = [i for i in os.listdir(archive_dir) if i != ".gitkeep"]
    print(f"Found {len(items)} items to clean up in {archive_dir}...")
    
    for item in items:
        item_path = os.path.join(archive_dir, item)
        # Attempt deletion up to 3 times in case of lingering background handles
        for attempt in range(3):
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, onexc=remove_readonly)
                else:
                    os.chmod(item_path, stat.S_IWRITE)
                    os.remove(item_path)
                print(f"Successfully deleted: {item}")
                break
            except Exception as e:
                if attempt == 2:
                    print(f"Could not delete {item}: {e}")
                else:
                    time.sleep(1)

    # Ensure .gitkeep exists
    gitkeep_path = os.path.join(archive_dir, ".gitkeep")
    with open(gitkeep_path, "a") as f:
        pass
        
    remaining = os.listdir(archive_dir)
    print(f"Local archive cleanup completed! Remaining items in {archive_dir}: {remaining}")

if __name__ == "__main__":
    main()
