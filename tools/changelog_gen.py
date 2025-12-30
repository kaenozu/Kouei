"""
Auto Changelog Generator
Scans the project for recent changes and updates CHANGELOG.md
"""
import os
import subprocess
from datetime import datetime

CHANGELOG_PATH = "CHANGELOG.md"

def get_git_commits(n=10):
    """Get last N git commits"""
    try:
        result = subprocess.run(
            ["git", "log", f"-n {n}", "--pretty=format:%h - %s (%ad)", "--date=short"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.split('\n')
    except:
        return ["No git history found or git not installed"]

def generate_changelog():
    """Generate or update CHANGELOG.md"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    commits = get_git_commits()
    
    new_entry = f"## [{date_str}] - Updated\n\n### Changes\n"
    for commit in commits:
        new_entry += f"- {commit}\n"
    new_entry += "\n"
    
    # Read existing content
    existing_content = ""
    if os.path.exists(CHANGELOG_PATH):
        with open(CHANGELOG_PATH, "r", encoding="utf-8") as f:
            existing_content = f.read()
    
    # Write new content at the top
    with open(CHANGELOG_PATH, "w", encoding="utf-8") as f:
        if not existing_content.startswith("# Changelog"):
            f.write("# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n")
        
        # Check if entry for today already exists to avoid duplicates
        if f"## [{date_str}]" not in existing_content:
            f.write(new_entry)
            if existing_content:
                # Append existing content after removing the title if it was there
                if existing_content.startswith("# Changelog"):
                    parts = existing_content.split("\n\n", 2)
                    if len(parts) > 2:
                        f.write(parts[2])
                else:
                    f.write(existing_content)
        else:
            f.write(existing_content)
            
    print(f"✅ Changelog updated: {CHANGELOG_PATH}")

if __name__ == "__main__":
    generate_changelog()
