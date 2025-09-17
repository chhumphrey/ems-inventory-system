# Render Deployment Configuration

This guide explains how to properly configure your EMS Inventory System on Render to prevent data loss during deployments.

## Environment Variables Setup

In your Render dashboard, set up the following environment variables:

### Required Environment Variables:
- `FLASK_ENV`: `production`
- `SECRET_KEY`: `your-secure-secret-key-here` (generate a new one for production)
- `USE_SENDGRID`: `true`
- `SENDGRID_API_KEY`: `your-sendgrid-api-key-here` (set this in Render dashboard)

### Optional Environment Variables:
- `MAIL_SUPPRESS_SEND`: `false` (set to true only for testing)
- `PASSWORD_RESET_EXPIRY`: `3600` (1 hour in seconds)

## Database Migration

The system now uses a proper migration script (`migrate_database.py`) that:

1. **Preserves existing data** during schema updates
2. **Safely adds new columns** (like first_name, last_name to user table)
3. **Creates new tables** (like password_reset_token) without affecting existing data
4. **Handles SQLite limitations** (like making columns nullable)

## How It Works

1. **Build Process**: During deployment, Render runs:
   ```bash
   pip install -r requirements.txt
   python migrate_database.py
   ```

2. **Migration Script**: The script checks what changes are needed and applies them safely:
   - If no tables exist → Creates initial schema + default data
   - If tables exist → Applies only necessary changes

3. **Data Safety**: Your existing data is never deleted or recreated

## Testing the Migration

To test locally before deploying:

```bash
# Test the migration script
python migrate_database.py

# Start the app
python run.py
```

## Rollback Plan

If something goes wrong:

1. **Immediate**: The previous deployment is still running
2. **Database**: Your data is preserved in Render's persistent storage
3. **Code**: You can revert to a previous commit in GitHub

## Security Notes

- The SendGrid API key is stored as a Render environment variable (not in code)
- The secret key should be changed from the default
- All sensitive data is kept out of the repository

## Monitoring

After deployment, check:

1. **Application logs** in Render dashboard
2. **Database migration logs** (printed during build)
3. **Email functionality** (test password reset)
4. **User data** (verify existing users are still there)

## Troubleshooting

If data is missing after deployment:

1. Check Render logs for migration errors
2. Verify environment variables are set correctly
3. Check if the migration script ran successfully
4. Contact support with specific error messages

---

**Important**: This configuration ensures your production data is safe during deployments while still allowing schema updates when needed.