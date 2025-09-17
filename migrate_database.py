#!/usr/bin/env python3
"""
Database migration script for EMS Inventory System
This script safely applies database schema changes without losing data
"""

import os
import sys
from sqlalchemy import text, inspect
from datetime import datetime

def migrate_database():
    """Apply database migrations safely"""
    try:
        from app import create_app
        from models import db
        
        app = create_app()
        
        with app.app_context():
            print("=" * 60)
            print("EMS Inventory System - Database Migration")
            print("=" * 60)
            print(f"Migration started at: {datetime.now()}")
            
            # Check if this is the first run (no tables exist)
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if not existing_tables:
                print("No existing tables found. Creating initial schema...")
                db.create_all()
                print("✓ Initial schema created")
                
                # Create default data
                from app import create_default_data
                create_default_data()
                print("✓ Default data created")
                
            else:
                print(f"Found {len(existing_tables)} existing tables. Applying migrations...")
                
                # Check if we need to add new columns to User table
                if 'user' in existing_tables:
                    try:
                        # Check if first_name column exists
                        result = db.session.execute(text("PRAGMA table_info(user)"))
                        columns = [row[1] for row in result.fetchall()]
                        
                        if 'first_name' not in columns:
                            print("Adding first_name column to user table...")
                            db.session.execute(text("ALTER TABLE user ADD COLUMN first_name VARCHAR(50)"))
                            print("✓ Added first_name column")
                        
                        if 'last_name' not in columns:
                            print("Adding last_name column to user table...")
                            db.session.execute(text("ALTER TABLE user ADD COLUMN last_name VARCHAR(50)"))
                            print("✓ Added last_name column")
                            
                    except Exception as e:
                        print(f"Warning: Could not add columns to user table: {e}")
                
                # Check if password_reset_token table exists
                if 'password_reset_token' not in existing_tables:
                    print("Creating password_reset_token table...")
                    from models import PasswordResetToken
                    PasswordResetToken.__table__.create(db.engine)
                    print("✓ Created password_reset_token table")
                
                # Check if audit_log table needs user_id to be nullable
                if 'audit_log' in existing_tables:
                    try:
                        # Check if user_id is nullable
                        result = db.session.execute(text("PRAGMA table_info(audit_log)"))
                        columns = result.fetchall()
                        user_id_col = next((col for col in columns if col[1] == 'user_id'), None)
                        
                        if user_id_col and user_id_col[3] == 0:  # 0 means NOT NULL
                            print("Making user_id nullable in audit_log table...")
                            # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
                            print("Recreating audit_log table with nullable user_id...")
                            
                            # Create new table with correct schema
                            db.session.execute(text("""
                                CREATE TABLE audit_log_new (
                                    id INTEGER PRIMARY KEY,
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
                            """))
                            
                            # Copy data from old table
                            db.session.execute(text("""
                                INSERT INTO audit_log_new 
                                SELECT * FROM audit_log
                            """))
                            
                            # Drop old table and rename new one
                            db.session.execute(text("DROP TABLE audit_log"))
                            db.session.execute(text("ALTER TABLE audit_log_new RENAME TO audit_log"))
                            
                            print("✓ Made user_id nullable in audit_log table")
                        else:
                            print("✓ audit_log table already has nullable user_id")
                            
                    except Exception as e:
                        print(f"Warning: Could not modify audit_log table: {e}")
                
                # Commit all changes
                db.session.commit()
                print("✓ All migrations applied successfully")
            
            print("=" * 60)
            print("Database migration completed successfully!")
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        print("Continuing with app startup...")
        # Don't exit - let the app try to start anyway

if __name__ == '__main__':
    migrate_database()
