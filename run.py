#!/usr/bin/env python3
"""
EMS Inventory Management System
Startup script for the application
"""

import os
import sys
from app import create_app

if __name__ == '__main__':
    # Set default configuration if not already set
    if not os.environ.get('SECRET_KEY'):
        os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    
    if not os.environ.get('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'sqlite:///ems_inventory.db'
    
    # Create and run the application
    app = create_app()
    
    print("=" * 60)
    print("EMS Inventory Management System")
    print("=" * 60)
    print(f"Database: {os.environ.get('DATABASE_URL')}")
    print(f"Admin Login: admin / admin123")
    print("=" * 60)
    print("Starting server...")
    print("Access the system at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
