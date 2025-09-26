#!/usr/bin/env python3
"""
Script to ensure admin user exists in production database
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import User, db

def ensure_admin_user():
    """Ensure admin user exists in the database"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if admin user exists
            admin_user = User.query.filter_by(username='admin').first()
            
            if not admin_user:
                print("Creating admin user...")
                admin_user = User(
                    username='admin',
                    email='admin@emsinventory.com',
                    password_hash=generate_password_hash('admin123'),
                    is_admin=True,
                    is_active=True
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✓ Admin user created successfully")
            else:
                print("✓ Admin user already exists")
                print(f"  Username: {admin_user.username}")
                print(f"  Email: {admin_user.email}")
                print(f"  Is Admin: {admin_user.is_admin}")
                print(f"  Is Active: {admin_user.is_active}")
            
            # Check total user count
            user_count = User.query.count()
            print(f"Total users in database: {user_count}")
            
        except Exception as e:
            print(f"Error ensuring admin user: {e}")

if __name__ == "__main__":
    ensure_admin_user()
