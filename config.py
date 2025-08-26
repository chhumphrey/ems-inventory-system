import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ems_inventory.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # EMS/Fire Service Color Scheme
    PRIMARY_COLOR = '#D32F2F'      # Fire Engine Red
    SECONDARY_COLOR = '#1976D2'    # EMS Blue
    ACCENT_COLOR = '#FFC107'       # Warning Yellow
    SUCCESS_COLOR = '#4CAF50'      # Safety Green
    DANGER_COLOR = '#F44336'       # Alert Red
    WARNING_COLOR = '#FF9800'      # Caution Orange
