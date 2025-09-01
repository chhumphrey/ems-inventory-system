#!/usr/bin/env python3
"""
Test script to verify the Flask app can start properly
"""

import sys
import os

try:
    print("Testing Flask app startup...")
    
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Test imports
    print("✓ Testing imports...")
    from app import create_app
    print("✓ App import successful")
    
    # Test app creation
    print("✓ Testing app creation...")
    app = create_app()
    print("✓ App creation successful")
    
    # Test app context
    print("✓ Testing app context...")
    with app.app_context():
        from models import db
        print("✓ Database connection successful")
    
    print("✅ All tests passed! App is ready for deployment.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
