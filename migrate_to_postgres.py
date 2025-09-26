#!/usr/bin/env python3
"""
Database migration script to move from SQLite to PostgreSQL
This script helps migrate existing data from SQLite to PostgreSQL
"""

import os
import sys
import sqlite3
import psycopg2
from urllib.parse import urlparse

def migrate_sqlite_to_postgres():
    """Migrate data from SQLite to PostgreSQL"""
    
    # Check if we have both databases configured
    sqlite_path = 'instance/ems_inventory.db'
    postgres_url = os.environ.get('DATABASE_URL')
    
    if not postgres_url:
        print("❌ No DATABASE_URL found. Please set up PostgreSQL first.")
        return False
    
    if not os.path.exists(sqlite_path):
        print("❌ SQLite database not found. Nothing to migrate.")
        return False
    
    print("🔄 Starting migration from SQLite to PostgreSQL...")
    
    try:
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Parse PostgreSQL URL
        parsed_url = urlparse(postgres_url)
        
        # Connect to PostgreSQL
        postgres_conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port,
            database=parsed_url.path[1:],  # Remove leading slash
            user=parsed_url.username,
            password=parsed_url.password
        )
        postgres_cursor = postgres_conn.cursor()
        
        # Get all tables from SQLite
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        print(f"📋 Found {len(tables)} tables to migrate: {tables}")
        
        # Migrate each table
        for table in tables:
            if table == 'sqlite_sequence':
                continue  # Skip SQLite system table
                
            print(f"🔄 Migrating table: {table}")
            
            # Get table structure
            sqlite_cursor.execute(f"PRAGMA table_info({table})")
            columns = sqlite_cursor.fetchall()
            
            # Get all data from SQLite table
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"  ⚠️  Table {table} is empty, skipping...")
                continue
            
            # Insert data into PostgreSQL
            # Note: This assumes the PostgreSQL tables already exist
            # The Flask app will create them with the correct structure
            
            column_names = [col[1] for col in columns]
            placeholders = ', '.join(['%s'] * len(column_names))
            insert_query = f"INSERT INTO {table} ({', '.join(column_names)}) VALUES ({placeholders})"
            
            try:
                postgres_cursor.executemany(insert_query, rows)
                postgres_conn.commit()
                print(f"  ✅ Migrated {len(rows)} rows to {table}")
            except Exception as e:
                print(f"  ❌ Error migrating {table}: {e}")
                postgres_conn.rollback()
        
        # Close connections
        sqlite_conn.close()
        postgres_conn.close()
        
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_sqlite_to_postgres()
