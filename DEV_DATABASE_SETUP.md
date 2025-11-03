# Development Database Setup

## Sharing Production Database with Development

The development environment can now connect to the production database for testing with real data.

## Setup Instructions

### Option 1: Using Environment Variable (Recommended)

1. **Get the production DATABASE_URL from Render:**
   - Go to your Render dashboard
   - Navigate to your PostgreSQL database service
   - Copy the "Internal Database URL" or "External Database URL"
   - It should look like: `postgresql://user:password@host:port/database`

2. **Set the DATABASE_URL in your local environment:**
   
   **Linux/Mac:**
   ```bash
   export DATABASE_URL="postgresql://user:password@host:port/database"
   ```
   
   **Windows (PowerShell):**
   ```powershell
   $env:DATABASE_URL="postgresql://user:password@host:port/database"
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   set DATABASE_URL=postgresql://user:password@host:port/database
   ```

3. **Or create a `.env` file** (if using python-dotenv):
   ```
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

### Option 2: Using Local SQLite (Default)

If `DATABASE_URL` is not set, the application will automatically use a local SQLite database (`ems_inventory.db`).

## Important Notes

⚠️ **WARNING**: Sharing the production database means:
- All changes in development will affect production data
- Be extremely careful when testing data modifications
- Consider using transactions or test data only
- Backup production data before extensive testing

✅ **Benefits**:
- Test with real data structure
- See actual production data in development
- No need to maintain separate test data sets
- Faster testing workflow

## Verification

After setting `DATABASE_URL`, start the application:
```bash
python run.py
```

You should see:
```
🐘 Using PostgreSQL database: postgresql+psycopg://...
```

If `DATABASE_URL` is not set, you'll see:
```
🗃️ Using local SQLite database (DATABASE_URL not set)
```

## Troubleshooting

### Connection Issues
- Verify the DATABASE_URL is correct
- Check if the database is accessible from your network (external URL)
- Ensure your IP is whitelisted if using external URL
- Verify credentials are correct

### SSL Connection Errors
- Add `?sslmode=require` to the DATABASE_URL if needed:
  ```
  DATABASE_URL="postgresql://user:password@host:port/database?sslmode=require"
  ```

### Still Using SQLite
- Verify DATABASE_URL environment variable is set: `echo $DATABASE_URL`
- Restart your terminal/IDE after setting the variable
- Check for typos in the variable name

