#!/usr/bin/env python3
"""
Gmail API Setup Script
This script helps you set up Gmail API for sending emails
"""

import os
import webbrowser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def setup_gmail_api():
    """Setup Gmail API credentials"""
    print("🔧 Gmail API Setup for EMS Inventory System")
    print("=" * 50)
    
    # Check if credentials file exists
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("\n📋 To set up Gmail API, follow these steps:")
        print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API:")
        print("   - Go to 'APIs & Services' > 'Library'")
        print("   - Search for 'Gmail API' and enable it")
        print("4. Create credentials:")
        print("   - Go to 'APIs & Services' > 'Credentials'")
        print("   - Click 'Create Credentials' > 'OAuth 2.0 Client IDs'")
        print("   - Choose 'Desktop application'")
        print("   - Download the JSON file and save as 'credentials.json'")
        print("\n5. Place credentials.json in this directory and run this script again")
        return False
    
    print("✅ credentials.json found")
    
    # Authenticate
    creds = None
    token_file = 'token.json'
    
    # Load existing token
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        print("✅ Found existing token")
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🔐 Starting OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            print("✅ OAuth flow completed")
        
        # Save credentials for next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        print("✅ Token saved to token.json")
    
    # Test Gmail API
    try:
        service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail API service created successfully")
        
        # Test by getting user profile
        profile = service.users().getProfile(userId='me').execute()
        print(f"✅ Authenticated as: {profile['emailAddress']}")
        
        print("\n🎉 Gmail API setup complete!")
        print("You can now use Gmail API to send emails.")
        print("\nTo enable Gmail API in your app, run:")
        print("USE_GMAIL_API=true python run.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail API test failed: {e}")
        return False

if __name__ == '__main__':
    setup_gmail_api()
