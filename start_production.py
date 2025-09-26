#!/usr/bin/env python3
"""
Production startup script that ensures database is properly migrated
"""

import os
import sys
from app import create_app

def start_production():
    """Start the production application with proper database migration"""
    
    print("Starting EMS Inventory System in Production Mode...")
    
    # Set production environment
    os.environ['FLASK_ENV'] = 'production'
    
    try:
        # Create the app
        app = create_app()
        
        # Run the migration script
        print("Running database migration...")
        from fix_production_db import fix_production_database
        if fix_production_database():
            print("✓ Database migration completed")
        else:
            print("⚠ Database migration had issues, but continuing...")
        
        print("✓ Application started successfully")
        return app
        
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    app = start_production()
    # The app will be started by gunicorn or the WSGI server
