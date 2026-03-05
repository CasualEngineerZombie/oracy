"""
Reset database script - deletes the SQLite database and runs migrations fresh.
"""
import os
import sys
import glob

def find_and_delete_db():
    """Find and delete SQLite database files."""
    # Look for common SQLite database names
    patterns = ['*.sqlite3', '*.db', 'db.sqlite3*']
    found = []
    
    for pattern in patterns:
        files = glob.glob(pattern)
        found.extend(files)
    
    if not found:
        print("No SQLite database files found in current directory.")
        return False
    
    print(f"Found database files: {found}")
    
    for db_file in found:
        try:
            os.remove(db_file)
            print(f"✅ Deleted: {db_file}")
        except Exception as e:
            print(f"❌ Error deleting {db_file}: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("Resetting database...")
    print("-" * 50)
    
    if find_and_delete_db():
        print("-" * 50)
        print("✅ Database deleted successfully!")
        print("\nNow run: uv run python manage.py migrate")
    else:
        print("-" * 50)
        print("⚠️  No database files to delete.")
        print("\nYou can proceed with: uv run python manage.py migrate")
