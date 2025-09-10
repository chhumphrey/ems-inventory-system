"""
SendGrid Email Service
Sends emails using SendGrid API (no SMTP server required)
"""

import os
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

def send_email_via_sendgrid(to_email, subject, html_content, text_content=None):
    """Send email using SendGrid API"""
    api_key = os.environ.get('SENDGRID_API_KEY')
    
    if not api_key:
        print("❌ SENDGRID_API_KEY not found in environment variables")
        return False
    
    try:
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        
        from_email = Email("chumphrey@wilsonvfcno1.org", "EMS Inventory System")
        to_email = To(to_email)
        
        # Create email content
        if text_content:
            content = Content("text/plain", text_content)
        else:
            content = Content("text/html", html_content)
        
        # Create mail object
        mail = Mail(from_email, to_email, subject, content)
        
        # Add HTML content if provided
        if html_content and text_content:
            mail.add_content(Content("text/html", html_content))
        
        # Send email
        response = sg.send(mail)
        
        print(f"🔍 SendGrid Response: {response.status_code}")
        print(f"🔍 Response Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 201, 202]:
            print(f"✅ Email sent successfully via SendGrid! Status: {response.status_code}")
            return True
        else:
            print(f"❌ SendGrid error: {response.status_code}")
            print(f"❌ Response body: {response.body}")
            return False
            
    except Exception as e:
        print(f"❌ SendGrid error: {e}")
        return False

def setup_sendgrid():
    """Setup instructions for SendGrid"""
    print("🔧 SendGrid Setup for EMS Inventory System")
    print("=" * 50)
    print("1. Go to https://sendgrid.com/")
    print("2. Sign up for a free account (100 emails/day)")
    print("3. Go to Settings > API Keys")
    print("4. Create a new API key with 'Mail Send' permissions")
    print("5. Copy the API key")
    print("6. Set environment variable:")
    print("   export SENDGRID_API_KEY='your-api-key-here'")
    print("7. Run: SENDGRID_API_KEY=your-key USE_SENDGRID=true python run.py")
    print("\n✅ SendGrid is much easier than Gmail API!")

if __name__ == '__main__':
    setup_sendgrid()
