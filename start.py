#!/usr/bin/env python3
"""
Startup script for production deployment
This script helps diagnose startup issues
"""

import os
import sys

def main():
    print("=" * 60)
    print("EMS Inventory System - Production Startup")
    print("=" * 60)
    
    # Print environment info
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}...")  # First 3 entries
    
    # Print environment variables
    print("\nEnvironment variables:")
    for key in ['FLASK_ENV', 'DATABASE_URL', 'SECRET_KEY', 'PORT']:
        value = os.environ.get(key, 'NOT SET')
        if key == 'SECRET_KEY' and value != 'NOT SET':
            value = f"{value[:8]}..."  # Only show first 8 chars
        print(f"  {key}: {value}")
    
    try:
        print("\nTesting imports...")
        from wsgi import app
        print("✓ WSGI app imported successfully")
        
        print("Testing app context...")
        with app.app_context():
            from models import db
            print("✓ Database connection successful")
        
        print("\n✅ All startup tests passed!")
        print("=" * 60)
        
        # Start the app
        port = int(os.environ.get('PORT', 5000))
        print(f"Starting server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
