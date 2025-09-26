#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Create the application instance
application = create_app()

# Run database migration in production
try:
    from fix_production_db import fix_production_database
    print("Running production database migration...")
    if fix_production_database():
        print("✓ Production database migration completed")
    else:
        print("⚠ Production database migration had issues, but continuing...")
except Exception as e:
    print(f"Database migration error: {e}")
    # Continue anyway - the app might still work

# For gunicorn compatibility
app = application

if __name__ == "__main__":
    application.run()
