#!/usr/bin/env python3
"""
Export local SQLite data for production import
This script exports all data to JSON files that can be imported into production
"""

import json
import os
from datetime import datetime
from app import create_app
from models import db, User, Location, Item, InventoryItem, Inventory, InventoryDetail, AuditLog

def export_data():
    """Export all data from local database to JSON files"""
    
    # Create export directory
    export_dir = "data_export"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Exporting EMS Inventory System Data")
        print("=" * 60)
        
        # Export Users
        print("Exporting Users...")
        users = User.query.all()
        users_data = []
        for user in users:
            user_data = {
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            users_data.append(user_data)
        
        with open(f"{export_dir}/users.json", 'w') as f:
            json.dump(users_data, f, indent=2)
        print(f"✓ Exported {len(users_data)} users")
        
        # Export Locations
        print("Exporting Locations...")
        locations = Location.query.all()
        locations_data = []
        for location in locations:
            location_data = {
                'name': location.name,
                'description': location.description,
                'location_type': location.location_type,
                'vehicle_id': location.vehicle_id,
                'created_at': location.created_at.isoformat() if location.created_at else None
            }
            locations_data.append(location_data)
        
        with open(f"{export_dir}/locations.json", 'w') as f:
            json.dump(locations_data, f, indent=2)
        print(f"✓ Exported {len(locations_data)} locations")
        
        # Export Items
        print("Exporting Items...")
        items = Item.query.all()
        items_data = []
        for item in items:
            item_data = {
                'name': item.name,
                'item_number': item.item_number,
                'manufacturer': item.manufacturer,
                'is_required': item.is_required,
                'required_quantity': item.required_quantity,
                'minimum_threshold': item.minimum_threshold,
                'created_at': item.created_at.isoformat() if item.created_at else None
            }
            items_data.append(item_data)
        
        with open(f"{export_dir}/items.json", 'w') as f:
            json.dump(items_data, f, indent=2)
        print(f"✓ Exported {len(items_data)} items")
        
        # Export Inventories
        print("Exporting Inventories...")
        inventories = Inventory.query.all()
        inventories_data = []
        for inventory in inventories:
            inventory_data = {
                'location_id': inventory.location_id,
                'user_id': inventory.user_id,
                'inventory_date': inventory.inventory_date.isoformat() if inventory.inventory_date else None,
                'notes': inventory.notes,
                'created_at': inventory.created_at.isoformat() if inventory.created_at else None
            }
            inventories_data.append(inventory_data)
        
        with open(f"{export_dir}/inventories.json", 'w') as f:
            json.dump(inventories_data, f, indent=2)
        print(f"✓ Exported {len(inventories_data)} inventories")
        
        # Export Inventory Items
        print("Exporting Inventory Items...")
        inventory_items = InventoryItem.query.all()
        inventory_items_data = []
        for inv_item in inventory_items:
            inv_item_data = {
                'item_id': inv_item.item_id,
                'location_id': inv_item.location_id,
                'quantity': inv_item.quantity,
                'expiration_date': inv_item.expiration_date.isoformat() if inv_item.expiration_date else None,
                'lot_number': inv_item.lot_number,
                'section': inv_item.section,
                'created_at': inv_item.created_at.isoformat() if inv_item.created_at else None
            }
            inventory_items_data.append(inv_item_data)
        
        with open(f"{export_dir}/inventory_items.json", 'w') as f:
            json.dump(inventory_items_data, f, indent=2)
        print(f"✓ Exported {len(inventory_items_data)} inventory items")
        
        # Export Audit Logs
        print("Exporting Audit Logs...")
        audit_logs = AuditLog.query.all()
        audit_logs_data = []
        for log in audit_logs:
            log_data = {
                'user_id': log.user_id,
                'action': log.action,
                'table_name': log.table_name,
                'record_id': log.record_id,
                'old_values': log.old_values,
                'new_values': log.new_values,
                'timestamp': log.timestamp.isoformat() if log.timestamp else None
            }
            audit_logs_data.append(log_data)
        
        with open(f"{export_dir}/audit_logs.json", 'w') as f:
            json.dump(audit_logs_data, f, indent=2)
        print(f"✓ Exported {len(audit_logs_data)} audit logs")
        
        # Create summary file
        summary = {
            'export_date': datetime.now().isoformat(),
            'total_users': len(users_data),
            'total_locations': len(locations_data),
            'total_items': len(items_data),
            'total_inventories': len(inventories_data),
            'total_inventory_items': len(inventory_items_data),
            'total_audit_logs': len(audit_logs_data)
        }
        
        with open(f"{export_dir}/export_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("\n" + "=" * 60)
        print("Export Complete!")
        print(f"Data exported to: {export_dir}/")
        print(f"Summary: {export_dir}/export_summary.json")
        print("=" * 60)
        
        return export_dir

if __name__ == '__main__':
    export_data()
