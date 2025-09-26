import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration - use PostgreSQL in production, SQLite in development
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url and database_url.startswith('postgresql://'):
        # Production: Use PostgreSQL from DATABASE_URL
        # Convert postgresql:// to postgresql+psycopg:// for psycopg3
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
        print(f"🐘 Using PostgreSQL database: {database_url[:50]}...")
    else:
        # Development: Use SQLite
        SQLALCHEMY_DATABASE_URI = 'sqlite:///ems_inventory.db'
        print("🗃️ Using SQLite database")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@emsinventory.com'
    
    # For development - use console backend
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'false').lower() in ['true', 'on', '1']
    
    # Gmail API settings
    USE_GMAIL_API = os.environ.get('USE_GMAIL_API', 'false').lower() in ['true', 'on', '1']
    
    # SendGrid API settings
    USE_SENDGRID = os.environ.get('USE_SENDGRID', 'false').lower() in ['true', 'on', '1']
    
    # Password Reset Configuration
    PASSWORD_RESET_EXPIRY = 3600  # 1 hour in seconds
    
    # EMS/Fire Service Color Scheme
    PRIMARY_COLOR = '#D32F2F'      # Fire Engine Red
    SECONDARY_COLOR = '#1976D2'    # EMS Blue
    ACCENT_COLOR = '#FFC107'       # Warning Yellow
    SUCCESS_COLOR = '#4CAF50'      # Safety Green
    DANGER_COLOR = '#F44336'       # Alert Red
    WARNING_COLOR = '#FF9800'      # Caution Orange
