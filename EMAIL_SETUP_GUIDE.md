# 📧 Email Setup Guide for EMS Inventory System

This guide shows you how to set up email sending without running your own SMTP server.

## 🚀 **Option 1: SendGrid (Recommended - Easiest)**

SendGrid is the easiest option with a generous free tier.

### Setup Steps:
1. **Sign up for SendGrid**:
   - Go to https://sendgrid.com/
   - Create a free account (100 emails/day)

2. **Get API Key**:
   - Go to Settings > API Keys
   - Click "Create API Key"
   - Choose "Restricted Access" > "Mail Send" permissions
   - Copy the API key

3. **Run the application**:
   ```bash
   export SENDGRID_API_KEY="your-api-key-here"
   USE_SENDGRID=true python run.py
   ```

### Test SendGrid:
```bash
python sendgrid_service.py
```

---

## 🔧 **Option 2: Gmail API**

Uses your existing Gmail account with OAuth2 authentication.

### Setup Steps:
1. **Google Cloud Console**:
   - Go to https://console.cloud.google.com/
   - Create a new project or select existing
   - Enable Gmail API

2. **Create Credentials**:
   - Go to APIs & Services > Credentials
   - Create OAuth 2.0 Client ID (Desktop application)
   - Download JSON file as `credentials.json`

3. **Setup**:
   ```bash
   python setup_gmail_api.py
   USE_GMAIL_API=true python run.py
   ```

---

## 📧 **Option 3: Office365 Graph API**

Uses your existing Office365 account with modern authentication.

### Setup Steps:
1. **Azure Portal**:
   - Go to https://portal.azure.com/
   - Register a new application
   - Add Mail.Send permissions

2. **Get credentials**:
   - Client ID, Client Secret, Tenant ID

3. **Configure**:
   ```bash
   USE_OFFICE365_API=true python run.py
   ```

---

## 🧪 **Option 4: Development Mode (Current)**

For testing without real email sending:

```bash
MAIL_SUPPRESS_SEND=true python run.py
```

Emails will be displayed in the console instead of being sent.

---

## 🎯 **Quick Start (SendGrid)**

1. **Get SendGrid API key** (5 minutes)
2. **Run**:
   ```bash
   export SENDGRID_API_KEY="your-key"
   USE_SENDGRID=true python run.py
   ```
3. **Test**: Go to http://localhost:5000/reset_password_request

---

## 📊 **Comparison**

| Option | Setup Time | Free Tier | Difficulty |
|--------|------------|-----------|------------|
| SendGrid | 5 minutes | 100 emails/day | ⭐ Easy |
| Gmail API | 15 minutes | Unlimited | ⭐⭐ Medium |
| Office365 | 20 minutes | Unlimited | ⭐⭐⭐ Hard |
| Development | 0 minutes | N/A | ⭐ Easiest |

---

## 🔍 **Troubleshooting**

### SendGrid Issues:
- Check API key is correct
- Verify "Mail Send" permission is enabled
- Check account is verified

### Gmail API Issues:
- Ensure `credentials.json` is in project root
- Check OAuth scopes include gmail.send
- Verify Gmail API is enabled in Google Cloud

### Office365 Issues:
- Check SMTP AUTH is enabled
- Verify app permissions in Azure
- Use app password if MFA is enabled

---

## 🎉 **Success!**

Once configured, your EMS Inventory System will send professional HTML emails with:
- ✅ EMS branding and colors
- ✅ Password reset functionality
- ✅ Professional templates
- ✅ No SMTP server required
