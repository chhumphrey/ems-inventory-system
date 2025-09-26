#!/usr/bin/env python3
"""
Simple script to fix production database schema issues
This adds missing columns to existing tables without data loss
"""

import sqlite3
import os
from datetime import datetime

def fix_production_database():
    """Fix production database by adding missing columns"""
    
    # Database path (adjust for production)
    db_path = os.path.join('instance', 'ems_inventory.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    print(f"Fixing database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if first_name column exists in user table
        cursor.execute("PRAGMA table_info(user)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'first_name' not in columns:
            print("Adding first_name column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN first_name VARCHAR(50)")
            print("✓ Added first_name column")
        else:
            print("✓ first_name column already exists")
            
        if 'last_name' not in columns:
            print("Adding last_name column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN last_name VARCHAR(50)")
            print("✓ Added last_name column")
        else:
            print("✓ last_name column already exists")
        
        # Check if password_reset_token table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='password_reset_token'")
        if not cursor.fetchone():
            print("Creating password_reset_token table...")
            cursor.execute("""
                CREATE TABLE password_reset_token (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token VARCHAR(100) NOT NULL UNIQUE,
                    expires_at DATETIME NOT NULL,
                    used BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            """)
            print("✓ Created password_reset_token table")
        else:
            print("✓ password_reset_token table already exists")
        
        # Check if audit_log user_id is nullable
        cursor.execute("PRAGMA table_info(audit_log)")
        audit_columns = cursor.fetchall()
        user_id_col = next((col for col in audit_columns if col[1] == 'user_id'), None)
        
        if user_id_col and user_id_col[3] == 0:  # 0 means NOT NULL
            print("Making user_id nullable in audit_log table...")
            
            # Create new table with nullable user_id
            cursor.execute("""
                CREATE TABLE audit_log_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action VARCHAR(100) NOT NULL,
                    table_name VARCHAR(100) NOT NULL,
                    record_id INTEGER,
                    old_values TEXT,
                    new_values TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            """)
            
            # Copy data from old table
            cursor.execute("INSERT INTO audit_log_new SELECT * FROM audit_log")
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE audit_log")
            cursor.execute("ALTER TABLE audit_log_new RENAME TO audit_log")
            
            print("✓ Made user_id nullable in audit_log table")
        else:
            print("✓ audit_log user_id is already nullable")
        
        conn.commit()
        print("✓ Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error fixing database: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_production_database()
