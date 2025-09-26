# PostgreSQL Setup for EMS Inventory System

This guide will help you set up PostgreSQL for persistent data storage on Render.

## Step 1: Create PostgreSQL Database on Render

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click "New +"** → **"PostgreSQL"**
3. **Configure the database**:
   - **Name**: `ems-inventory-db`
   - **Database**: `ems_inventory`
   - **User**: `ems_user` (or leave default)
   - **Region**: Choose closest to your app
   - **Plan**: Free tier is fine for development

4. **Click "Create Database"**

## Step 2: Get Database Connection String

1. **Click on your new database**
2. **Go to "Connections" tab**
3. **Copy the "External Database URL"** - it looks like:
   ```
   postgresql://ems_user:password@dpg-xxxxx-a.oregon-postgres.render.com/ems_inventory
   ```

## Step 3: Update Your Web Service

1. **Go to your web service** (ems-inventory-system)
2. **Go to "Environment" tab**
3. **Add new environment variable**:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the PostgreSQL connection string from Step 2

## Step 4: Deploy the Updated Code

1. **Commit and push** the updated code to GitHub
2. **Render will automatically deploy** the changes
3. **The app will automatically**:
   - Connect to PostgreSQL
   - Create all necessary tables
   - Initialize with default data

## Step 5: Verify the Setup

1. **Visit your app**: https://ems-inventory-system.onrender.com
2. **Login with**: admin / admin123
3. **Add some test data** (items, locations, etc.)
4. **Restart the app** (go to Render dashboard → your service → "Manual Deploy" → "Deploy latest commit")
5. **Check that your data persists** after restart

## Migration from SQLite (Optional)

If you have existing data in SQLite that you want to migrate:

1. **Set up PostgreSQL** (Steps 1-3 above)
2. **Run the migration script locally**:
   ```bash
   # Set the DATABASE_URL environment variable
   export DATABASE_URL="postgresql://ems_user:password@dpg-xxxxx-a.oregon-postgres.render.com/ems_inventory"
   
   # Run the migration
   python migrate_to_postgres.py
   ```
3. **Deploy the updated code**

## Troubleshooting

### Database Connection Issues
- **Check the DATABASE_URL** is correct
- **Verify the database is running** on Render
- **Check the database credentials**

### Migration Issues
- **Ensure PostgreSQL is accessible** from your local machine
- **Check that all required tables exist** in PostgreSQL
- **Verify data types match** between SQLite and PostgreSQL

### App Won't Start
- **Check the logs** in Render dashboard
- **Verify environment variables** are set correctly
- **Ensure all dependencies** are installed

## Benefits of PostgreSQL

✅ **Persistent data** - survives app restarts
✅ **Better performance** - optimized for production
✅ **Scalability** - can handle more users and data
✅ **Backup and recovery** - automatic backups on Render
✅ **Concurrent access** - multiple users can access simultaneously

## Cost

- **Free tier**: 1GB storage, 1GB RAM
- **Paid tiers**: Start at $7/month for more storage and performance
- **Perfect for small to medium applications**

---

**Need help?** Check the Render documentation or contact support.
