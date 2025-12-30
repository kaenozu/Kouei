"""
Automatic Database Backup Script
Backs up race_data.db and models to backups/ directory
Run this daily via cron/Task Scheduler
"""
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

BACKUP_DIR = "backups"
DB_PATH = "data/race_data.db"
MODELS_DIR = "models"
KEEP_DAYS = 7

def backup_database():
    """Backup database file"""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return False
    
    # Create backup directory
    Path(BACKUP_DIR).mkdir(exist_ok=True)
    
    # Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup DB
    db_backup = f"{BACKUP_DIR}/race_data_{timestamp}.db"
    shutil.copy2(DB_PATH, db_backup)
    db_size = os.path.getsize(db_backup) / (1024 * 1024)  # MB
    print(f"✅ Database backed up: {db_backup} ({db_size:.2f} MB)")
    
    # Backup models directory
    if os.path.exists(MODELS_DIR):
        models_backup = f"{BACKUP_DIR}/models_{timestamp}"
        shutil.copytree(MODELS_DIR, models_backup, dirs_exist_ok=True)
        print(f"✅ Models backed up: {models_backup}")
    
    return True

def cleanup_old_backups():
    """Remove backups older than KEEP_DAYS"""
    if not os.path.exists(BACKUP_DIR):
        return
    
    cutoff_date = datetime.now() - timedelta(days=KEEP_DAYS)
    removed = 0
    
    for filename in os.listdir(BACKUP_DIR):
        filepath = os.path.join(BACKUP_DIR, filename)
        
        # Check file modification time
        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        
        if file_time < cutoff_date:
            if os.path.isfile(filepath):
                os.remove(filepath)
                removed += 1
            elif os.path.isdir(filepath):
                shutil.rmtree(filepath)
                removed += 1
    
    if removed > 0:
        print(f"🗑️  Removed {removed} old backups (>{KEEP_DAYS} days)")

def main():
    print("=" * 60)
    print("💾 Kyotei AI - Database Backup")
    print("=" * 60)
    
    # Perform backup
    if backup_database():
        # Cleanup old backups
        cleanup_old_backups()
        print("\n✅ Backup completed successfully")
        return 0
    else:
        print("\n❌ Backup failed")
        return 1

if __name__ == "__main__":
    exit(main())
