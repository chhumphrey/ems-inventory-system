#!/usr/bin/env python3
"""
Import exported data into production environment
This script imports JSON data files into the production database
"""

import json
import os
from datetime import datetime
from app import create_app
from models import db, User, Location, Item, InventoryItem, Inventory, InventoryDetail, AuditLog

def import_data(export_dir="data_export"):
    """Import data from JSON files into the database"""
    
    if not os.path.exists(export_dir):
        print(f"❌ Export directory '{export_dir}' not found!")
        return False
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Importing EMS Inventory System Data")
        print("=" * 60)
        
        try:
            # Import Users
            print("Importing Users...")
            if os.path.exists(f"{export_dir}/users.json"):
                with open(f"{export_dir}/users.json", 'r') as f:
                    users_data = json.load(f)
                
                for user_data in users_data:
                    # Check if user already exists
                    existing_user = User.query.filter_by(username=user_data['username']).first()
                    if not existing_user:
                        user = User(
                            username=user_data['username'],
                            email=user_data['email'],
                            is_admin=user_data['is_admin']
                        )
                        # Set default password for imported users
                        user.set_password('changeme123')
                        db.session.add(user)
                        print(f"  ✓ Added user: {user_data['username']}")
                    else:
                        print(f"  - User already exists: {user_data['username']}")
                
                db.session.commit()
                print(f"✓ Imported {len(users_data)} users")
            
            # Import Locations
            print("Importing Locations...")
            if os.path.exists(f"{export_dir}/locations.json"):
                with open(f"{export_dir}/locations.json", 'r') as f:
                    locations_data = json.load(f)
                
                for location_data in locations_data:
                    # Check if location already exists
                    existing_location = Location.query.filter_by(name=location_data['name']).first()
                    if not existing_location:
                        location = Location(
                            name=location_data['name'],
                            description=location_data['description'],
                            location_type=location_data['location_type'],
                            vehicle_id=location_data['vehicle_id']
                        )
                        db.session.add(location)
                        print(f"  ✓ Added location: {location_data['name']}")
                    else:
                        print(f"  - Location already exists: {location_data['name']}")
                
                db.session.commit()
                print(f"✓ Imported {len(locations_data)} locations")
            
            # Import Items
            print("Importing Items...")
            if os.path.exists(f"{export_dir}/items.json"):
                with open(f"{export_dir}/items.json", 'r') as f:
                    items_data = json.load(f)
                
                for item_data in items_data:
                    # Check if item already exists
                    existing_item = Item.query.filter_by(item_number=item_data['item_number']).first()
                    if not existing_item:
                        item = Item(
                            name=item_data['name'],
                            item_number=item_data['item_number'],
                            manufacturer=item_data['manufacturer'],
                            is_required=item_data['is_required'],
                            required_quantity=item_data['required_quantity'],
                            minimum_threshold=item_data['minimum_threshold']
                        )
                        db.session.add(item)
                        print(f"  ✓ Added item: {item_data['name']}")
                    else:
                        print(f"  - Item already exists: {item_data['name']}")
                
                db.session.commit()
                print(f"✓ Imported {len(items_data)} items")
            
            # Import Inventories (need to handle location_id mapping)
            print("Importing Inventories...")
            if os.path.exists(f"{export_dir}/inventories.json"):
                with open(f"{export_dir}/inventories.json", 'r') as f:
                    inventories_data = json.load(f)
                
                # Create location name to ID mapping
                location_map = {}
                for location in Location.query.all():
                    location_map[location.name] = location.id
                
                for inventory_data in inventories_data:
                    # For now, skip inventories as they need proper location mapping
                    # You can implement this later if needed
                    print(f"  - Skipping inventory (location mapping needed)")
                
                print(f"⚠️  Inventories skipped (location mapping required)")
            
            # Import Inventory Items (need to handle ID mappings)
            print("Importing Inventory Items...")
            if os.path.exists(f"{export_dir}/inventory_items.json"):
                print("  - Skipping inventory items (requires inventory and location mapping)")
                print("⚠️  Inventory items skipped (complex mapping required)")
            
            # Import Audit Logs (optional)
            print("Importing Audit Logs...")
            if os.path.exists(f"{export_dir}/audit_logs.json"):
                print("  - Skipping audit logs (production environment)")
                print("⚠️  Audit logs skipped (not needed in production)")
            
            print("\n" + "=" * 60)
            print("Import Complete!")
            print("=" * 60)
            print("⚠️  IMPORTANT NOTES:")
            print("1. Users imported with default password: 'changeme123'")
            print("2. Inventories and Inventory Items skipped (complex mapping)")
            print("3. Change all user passwords after import")
            print("4. Verify all data imported correctly")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    import_data()
