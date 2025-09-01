from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
import os

from config import Config
from models import db, User, Location, Item, InventoryItem, Inventory, InventoryDetail, AuditLog
from forms import LoginForm, UserForm, LocationForm, ItemForm, InventoryItemForm, InventoryForm, SearchForm
from routes import main_bp, admin_bp, inventory_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        create_default_data()
    
    return app

def create_default_data():
    """Create default admin user and sample data if database is empty"""
    if User.query.first() is None:
        # Create default admin user
        admin = User(
            username='admin',
            email='admin@emscompany.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create sample locations
        locations = [
            Location(name='Ambulance 1', description='Primary ambulance', location_type='ambulance'),
            Location(name='Supply Room A', description='Main supply room', location_type='supply_room'),
            Location(name='Go Bag 1', description='First responder go bag', location_type='go_bag', vehicle_id='Truck 1'),
            Location(name='Go Bag 2', description='Second responder go bag', location_type='go_bag', vehicle_id='Truck 2')
        ]
        
        for location in locations:
            db.session.add(location)
        
        # Create sample items
        items = [
            Item(name='Normal Saline 0.9% 1000ml', item_number='NS-1000', manufacturer='Baxter', 
                 is_required=True, required_quantity=4, minimum_threshold=2),
            Item(name='4x4 Gauze Pads', item_number='GAUZE-4X4', manufacturer='Johnson & Johnson', 
                 is_required=True, required_quantity=20, minimum_threshold=10),
            Item(name='Adhesive Tape 1 inch', item_number='TAPE-1IN', manufacturer='3M', 
                 is_required=True, required_quantity=6, minimum_threshold=3),
            Item(name='Gloves Large', item_number='GLOVES-L', manufacturer='Medline', 
                 is_required=True, required_quantity=10, minimum_threshold=5)
        ]
        
        for item in items:
            db.session.add(item)
        
        db.session.commit()

# Application instance for gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
