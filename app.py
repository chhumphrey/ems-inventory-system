from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import text, inspect
import os
import secrets
import hashlib

from config import Config
from models import db, User, Location, Item, InventoryItem, Inventory, InventoryDetail, AuditLog, PasswordResetToken
from forms import LoginForm, UserForm, LocationForm, ItemForm, InventoryItemForm, InventoryForm, SearchForm
from routes import main_bp, admin_bp, inventory_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Configure email for development
    if app.config.get('MAIL_SUPPRESS_SEND', False):
        app.config['MAIL_SUPPRESS_SEND'] = True
        app.config['MAIL_DEBUG'] = True
    
    mail = Mail(app)
    
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
    
    # Initialize database
    with app.app_context():
        try:
            # Debug: Print database configuration
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            print(f"Database URI: {db_uri[:50]}...")
            
            # Check if we're using PostgreSQL (production) or SQLite (development)
            is_postgres = 'postgresql' in db_uri
            
            if is_postgres:
                print("🐘 Using PostgreSQL database")
                try:
                    # Test database connection first
                    from sqlalchemy import text
                    db.session.execute(text("SELECT 1"))
                    print("✓ PostgreSQL connection successful")
                    
                    # Create tables
                    db.create_all()
                    migrate_database()
                    
                    # Check if we have data
                    user_count = User.query.count()
                    if user_count > 0:
                        print("✓ PostgreSQL database connected - data exists")
                        ensure_admin_user()
                    else:
                        print("✓ PostgreSQL database connected - no data, initializing...")
                        create_default_data()
                        print("✓ PostgreSQL database initialized with default data")
                        
                except Exception as pg_error:
                    print(f"❌ PostgreSQL connection failed: {pg_error}")
                    print("🔄 Falling back to SQLite for this session")
                    # Fall back to SQLite if PostgreSQL fails
                    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ems_inventory.db'
                    db.init_app(app)
                    db.create_all()
                    migrate_database()
                    create_default_data()
                    print("✓ Fallback to SQLite completed")
            else:
                print("🗃️ Using SQLite database")
                # For SQLite, check if data exists first
                try:
                    user_count = User.query.count()
                    if user_count > 0:
                        print("✓ SQLite database connected - data exists")
                        ensure_admin_user()
                    else:
                        print("✓ SQLite database connected - no data, initializing...")
                        migrate_database()
                        create_default_data()
                        print("✓ SQLite database initialized with default data")
                except Exception as db_error:
                    print(f"SQLite query failed, initializing fresh database: {db_error}")
                    db.create_all()
                    migrate_database()
                    create_default_data()
                    print("✓ Fresh SQLite database created with default data")
                
        except Exception as e:
            print(f"Database initialization error: {e}")
            # Try to continue anyway - don't let database issues crash the app
            try:
                # At minimum, ensure admin user exists
                ensure_admin_user()
            except Exception as e2:
                print(f"Error ensuring admin user: {e2}")
            pass
    
    return app

def migrate_database():
    """Migrate database schema to add new columns and tables"""
    try:
        from sqlalchemy import text, inspect
        
        # Check if first_name column exists in user table
        inspector = inspect(db.engine)
        user_columns = [col['name'] for col in inspector.get_columns('user')]
        
        if 'first_name' not in user_columns:
            print("Adding first_name column to user table...")
            try:
                db.engine.execute(text("ALTER TABLE user ADD COLUMN first_name VARCHAR(50)"))
                print("✓ Added first_name column")
            except Exception as e:
                print(f"Error adding first_name column: {e}")
                # Continue anyway
        
        if 'last_name' not in user_columns:
            print("Adding last_name column to user table...")
            try:
                db.engine.execute(text("ALTER TABLE user ADD COLUMN last_name VARCHAR(50)"))
                print("✓ Added last_name column")
            except Exception as e:
                print(f"Error adding last_name column: {e}")
                # Continue anyway
        
        # Check if password_reset_token table exists
        tables = inspector.get_table_names()
        if 'password_reset_token' not in tables:
            print("Creating password_reset_token table...")
            db.engine.execute(text("""
                CREATE TABLE password_reset_token (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token VARCHAR(100) NOT NULL UNIQUE,
                    expires_at DATETIME NOT NULL,
                    used BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            """))
            print("✓ Created password_reset_token table")
        
        # Check if audit_log user_id is nullable
        audit_columns = inspector.get_columns('audit_log')
        user_id_col = next((col for col in audit_columns if col['name'] == 'user_id'), None)
        
        if user_id_col and not user_id_col['nullable']:
            print("Making user_id nullable in audit_log table...")
            # For SQLite, we need to recreate the table
            db.engine.execute(text("""
                CREATE TABLE audit_log_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action VARCHAR(100) NOT NULL,
                    table_name VARCHAR(100) NOT NULL,
                    record_id INTEGER,
                    old_values TEXT,
                    new_values TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            """))
            
            # Copy data from old table
            db.engine.execute(text("INSERT INTO audit_log_new SELECT * FROM audit_log"))
            
            # Drop old table and rename new one
            db.engine.execute(text("DROP TABLE audit_log"))
            db.engine.execute(text("ALTER TABLE audit_log_new RENAME TO audit_log"))
            
            print("✓ Made user_id nullable in audit_log table")
        
        print("✓ Database migration completed")
        
    except Exception as e:
        print(f"Database migration error: {e}")
        # Continue anyway - the app might still work

def ensure_admin_user():
    """Ensure admin user exists in the database"""
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
            print("✓ Admin user exists")
            
    except Exception as e:
        print(f"Error ensuring admin user: {e}")

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

def send_password_reset_email(user, token):
    """Send password reset email to user"""
    from gmail_service import send_email_via_gmail
    from sendgrid_service import send_email_via_sendgrid
    
    # Try SendGrid first (easiest)
    if app.config.get('USE_SENDGRID', False):
        subject = 'Password Reset Request - EMS Inventory System'
        reset_url = f"http://localhost:5000/reset_password/{token}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #D32F2F; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
                <h2 style="margin: 0;"><i class="fas fa-ambulance"></i> EMS Inventory System</h2>
            </div>
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 5px 5px;">
                <h3 style="color: #333;">Password Reset Request</h3>
                <p>Hello {user.get_full_name()},</p>
                <p>You have requested to reset your password for the EMS Inventory Management System.</p>
                <p>Click the button below to reset your password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background-color: #1976D2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
                </div>
                <p style="color: #666; font-size: 14px;">This link will expire in 1 hour for security reasons.</p>
                <p style="color: #666; font-size: 14px;">If you didn't request this password reset, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    Volunteer Fire Company EMS Group<br>
                    This is an automated message, please do not reply.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Password Reset Request - EMS Inventory System
Hello {user.get_full_name()},
You have requested to reset your password for the EMS Inventory Management System.
Click the link below to reset your password:
{reset_url}
This link will expire in 1 hour for security reasons.
If you didn't request this password reset, please ignore this email.
Volunteer Fire Company EMS Group
This is an automated message, please do not reply.
        """
        
        return send_email_via_sendgrid(user.email, subject, html_content, text_content)
    
    # Try Gmail API second
    elif app.config.get('USE_GMAIL_API', False):
        subject = 'Password Reset Request - EMS Inventory System'
        reset_url = f"http://localhost:5000/reset_password/{token}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #D32F2F; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
                <h2 style="margin: 0;"><i class="fas fa-ambulance"></i> EMS Inventory System</h2>
            </div>
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 5px 5px;">
                <h3 style="color: #333;">Password Reset Request</h3>
                <p>Hello {user.get_full_name()},</p>
                <p>You have requested to reset your password for the EMS Inventory Management System.</p>
                <p>Click the button below to reset your password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background-color: #1976D2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
                </div>
                <p style="color: #666; font-size: 14px;">This link will expire in 1 hour for security reasons.</p>
                <p style="color: #666; font-size: 14px;">If you didn't request this password reset, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    Volunteer Fire Company EMS Group<br>
                    This is an automated message, please do not reply.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Password Reset Request - EMS Inventory System
Hello {user.get_full_name()},
You have requested to reset your password for the EMS Inventory Management System.
Click the link below to reset your password:
{reset_url}
This link will expire in 1 hour for security reasons.
If you didn't request this password reset, please ignore this email.
Volunteer Fire Company EMS Group
This is an automated message, please do not reply.
        """
        
        return send_email_via_gmail(user.email, subject, html_content, text_content)
    
    # Fallback to SMTP
    from flask_mail import Message
    
    msg = Message(
        subject='Password Reset Request - EMS Inventory System',
        recipients=[user.email],
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    
    reset_url = f"http://localhost:5000/reset_password/{token}"
    
    msg.html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #D32F2F; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
            <h2 style="margin: 0;"><i class="fas fa-ambulance"></i> EMS Inventory System</h2>
        </div>
        <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 5px 5px;">
            <h3 style="color: #333;">Password Reset Request</h3>
            <p>Hello {user.get_full_name()},</p>
            <p>You have requested to reset your password for the EMS Inventory Management System.</p>
            <p>Click the button below to reset your password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background-color: #1976D2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
            </div>
            <p style="color: #666; font-size: 14px;">This link will expire in 1 hour for security reasons.</p>
            <p style="color: #666; font-size: 14px;">If you didn't request this password reset, please ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
            <p style="color: #999; font-size: 12px; text-align: center;">
                Volunteer Fire Company EMS Group<br>
                This is an automated message, please do not reply.
            </p>
        </div>
    </body>
    </html>
    """
    
    msg.body = f"""
Password Reset Request - EMS Inventory System

Hello {user.get_full_name()},

You have requested to reset your password for the EMS Inventory Management System.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you didn't request this password reset, please ignore this email.

Volunteer Fire Company EMS Group
This is an automated message, please do not reply.
    """
    
    try:
        if app.config.get('MAIL_SUPPRESS_SEND', False):
            # In development mode, print email to console
            print("=" * 60)
            print("EMAIL WOULD BE SENT:")
            print("=" * 60)
            print(f"To: {msg.recipients[0]}")
            print(f"From: {msg.sender}")
            print(f"Subject: {msg.subject}")
            print("-" * 60)
            print("HTML Content:")
            print(msg.html)
            print("-" * 60)
            print("Text Content:")
            print(msg.body)
            print("=" * 60)
            return True
        else:
            from flask_mail import Mail
            mail = Mail(app)
            mail.send(msg)
            return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def generate_password_reset_token(user):
    """Generate a secure password reset token for user"""
    # Create a secure token
    token = secrets.token_urlsafe(32)
    
    # Set expiration time (1 hour from now)
    expires_at = datetime.utcnow() + timedelta(seconds=app.config['PASSWORD_RESET_EXPIRY'])
    
    # Create token record
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    
    # Remove any existing tokens for this user
    PasswordResetToken.query.filter_by(user_id=user.id, used=False).delete()
    
    # Save new token
    db.session.add(reset_token)
    db.session.commit()
    
    return token

def verify_password_reset_token(token):
    """Verify password reset token and return user if valid"""
    reset_token = PasswordResetToken.query.filter_by(
        token=token, 
        used=False
    ).first()
    
    if not reset_token:
        return None
    
    # Check if token is expired
    if datetime.utcnow() > reset_token.expires_at:
        return None
    
    return reset_token.user

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
