#!/usr/bin/env python3
"""
Debug script to check production database state
"""

import os
import sqlite3

def debug_production_db():
    """Debug production database to see what's missing"""
    
    # Try multiple possible database paths
    possible_paths = [
        os.path.join('instance', 'ems_inventory.db'),
        os.path.join(os.getcwd(), 'instance', 'ems_inventory.db'),
        'ems_inventory.db',
        os.path.join('/opt/render/project/src', 'instance', 'ems_inventory.db'),
        os.path.join('/app', 'instance', 'ems_inventory.db')
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print(f"Database not found in any of these locations: {possible_paths}")
        return
    
    print(f"Found database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check user table structure
        print("\n=== USER TABLE STRUCTURE ===")
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - nullable: {col[3] == 0}")
        
        # Check if first_name and last_name exist
        column_names = [col[1] for col in columns]
        print(f"\nfirst_name exists: {'first_name' in column_names}")
        print(f"last_name exists: {'last_name' in column_names}")
        
        # Check user data
        print("\n=== USER DATA ===")
        cursor.execute("SELECT id, username, first_name, last_name FROM user LIMIT 5")
        users = cursor.fetchall()
        for user in users:
            print(f"  ID: {user[0]}, Username: {user[1]}, First: {user[2]}, Last: {user[3]}")
        
        # Check tables
        print("\n=== ALL TABLES ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  {table[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error debugging database: {e}")

if __name__ == "__main__":
    debug_production_db()
