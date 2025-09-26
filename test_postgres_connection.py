#!/usr/bin/env python3
"""
Test PostgreSQL connection to diagnose the issue
"""

import os
import psycopg2
from urllib.parse import urlparse

def test_postgres_connection():
    """Test PostgreSQL connection"""
    
    database_url = "postgresql://ems_inventory_user:UiEmnfMBgWYtJ4pjEkqS5AGmffH98OCO@dpg-d3b12bjuibrs73f3qs10-a.ohio-postgres.render.com/ems_inventory"
    
    print(f"Testing connection to: {database_url[:50]}...")
    
    try:
        # Parse the URL
        parsed_url = urlparse(database_url)
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port,
            database=parsed_url.path[1:],  # Remove leading slash
            user=parsed_url.username,
            password=parsed_url.password
        )
        
        # Test the connection
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        print("✅ PostgreSQL connection successful!")
        print(f"✅ Test query result: {result}")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

if __name__ == "__main__":
    test_postgres_connection()
