#!/usr/bin/env python3
"""
Migration script to add email verification columns to users table
This fixes the "no such column: users.email_verified" error
"""

import sqlite3
import sys
import io
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def migrate_database():
    """Add email verification columns to users table"""
    
    # Get database path
    backend_dir = Path(__file__).parent
    project_dir = backend_dir.parent
    database_dir = project_dir / 'database'
    db_path = database_dir / 'antitheft.db'
    
    if not db_path.exists():
        print("Database file not found. It will be created automatically when you restart the backend.")
        return
    
    print(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add email_verified column if it doesn't exist
        if 'email_verified' not in columns:
            print("Adding email_verified column...")
            cursor.execute("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0")
            print("✓ Added email_verified column")
        else:
            print("✓ email_verified column already exists")
        
        # Add verification_code column if it doesn't exist
        if 'verification_code' not in columns:
            print("Adding verification_code column...")
            cursor.execute("ALTER TABLE users ADD COLUMN verification_code VARCHAR(6)")
            print("✓ Added verification_code column")
        else:
            print("✓ verification_code column already exists")
        
        # Add verification_code_expires column if it doesn't exist
        if 'verification_code_expires' not in columns:
            print("Adding verification_code_expires column...")
            cursor.execute("ALTER TABLE users ADD COLUMN verification_code_expires DATETIME")
            print("✓ Added verification_code_expires column")
        else:
            print("✓ verification_code_expires column already exists")
        
        # Set existing users as verified (backward compatibility)
        cursor.execute("UPDATE users SET email_verified = 1 WHERE email_verified IS NULL OR email_verified = 0")
        print("✓ Set existing users as email_verified = True")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Database migration completed successfully!")
        print("   You can now restart your backend server.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    migrate_database()
