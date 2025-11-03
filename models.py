from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Soft delete
    deleted_at = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get user's full name, fallback to username if not set"""
        try:
            # Safely access first_name and last_name attributes
            first_name = getattr(self, 'first_name', None)
            last_name = getattr(self, 'last_name', None)
            
            if first_name and last_name:
                return f"{first_name} {last_name}"
            elif first_name:
                return first_name
            elif last_name:
                return last_name
            else:
                return self.username
        except Exception:
            # Fallback to username if any error occurs
            return self.username

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    location_type = db.Column(db.String(50))  # ambulance, supply_room, go_bag
    vehicle_id = db.Column(db.String(50))  # for go bags
    has_sections = db.Column(db.Boolean, default=False)  # Whether this location has sections
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Soft delete
    deleted_at = db.Column(db.DateTime)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    item_number = db.Column(db.String(100))
    manufacturer = db.Column(db.String(200))
    is_required = db.Column(db.Boolean, default=False)
    required_quantity = db.Column(db.Integer, default=0)
    minimum_threshold = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Soft delete
    deleted_at = db.Column(db.DateTime)

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    section = db.Column(db.String(5))  # Section identifier (5 characters max)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    expiration_date = db.Column(db.Date)
    lot_number = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Soft delete
    deleted_at = db.Column(db.DateTime)
    
    # Relationships
    item = db.relationship('Item', backref='inventory_items')
    location = db.relationship('Location', backref='inventory_items')

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    inventory_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Soft delete
    deleted_at = db.Column(db.DateTime)
    
    # Relationships
    location = db.relationship('Location', backref='inventories')
    user = db.relationship('User', backref='inventories')

class InventoryDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    expiration_date = db.Column(db.Date)
    lot_number = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Soft delete
    deleted_at = db.Column(db.DateTime)
    
    # Relationships
    inventory = db.relationship('Inventory', backref='details')
    item = db.relationship('Item', backref='inventory_details')

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='password_reset_tokens')

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)
    new_values = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')

# Attendance Module Models

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Soft delete
    deleted_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Organization {self.name}>'

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Optional link to user account
    badge_number = db.Column(db.String(50))
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    membership_type = db.Column(db.String(50))  # active, reserve, probationary, etc.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Soft delete
    deleted_at = db.Column(db.DateTime)
    
    # Relationships
    organization = db.relationship('Organization', backref='members')
    user = db.relationship('User', backref='member_profile')
    
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def __repr__(self):
        return f'<Member {self.get_full_name()}>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # training, drill, incident, meeting, other
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Soft delete
    deleted_at = db.Column(db.DateTime)
    
    # Relationships
    organization = db.relationship('Organization', backref='events')
    location = db.relationship('Location', backref='events')
    created_by_user = db.relationship('User', backref='created_events')
    
    def __repr__(self):
        return f'<Event {self.title}>'

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # present, late, excused, absent
    method = db.Column(db.String(20), nullable=False)  # roster, qr, pin, kiosk, admin
    check_in_time = db.Column(db.DateTime)
    check_out_time = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='attendance_records')
    event = db.relationship('Event', backref='attendance_records')
    member = db.relationship('Member', backref='attendance_records')
    created_by_user = db.relationship('User', backref='recorded_attendance')
    
    def __repr__(self):
        return f'<AttendanceRecord {self.member_id} at {self.event_id}>'
