# 🚀 EMS Inventory System - Render Deployment Guide

## Overview
This guide will help you deploy the EMS Inventory System to Render, a modern cloud platform that integrates seamlessly with GitHub.

## Prerequisites
- GitHub account with your EMS Inventory System repository
- Render account (free at [render.com](https://render.com))

## Step-by-Step Deployment

### 1. Prepare Your Repository
✅ All necessary files are already in place:
- `render.yaml` - Render configuration
- `requirements.txt` - Python dependencies (including gunicorn)
- `Procfile` - Alternative deployment method
- `config.py` - Production-ready configuration
- `run.py` - Updated for production

### 2. Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Authorize Render to access your repositories

### 3. Deploy Your Application
1. **Click "New +"** in your Render dashboard
2. **Select "Web Service"**
3. **Connect your GitHub repository:**
   - Choose your EMS Inventory System repository
   - Select the main branch (usually `main` or `master`)

4. **Configure the service:**
   - **Name:** `ems-inventory-system`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free tier (or upgrade as needed)

5. **Set Environment Variables:**
   - `SECRET_KEY`: Generate a secure random key (use: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `FLASK_ENV`: `production`
   - `DATABASE_URL`: Will be automatically set by Render

6. **Click "Create Web Service"**

### 4. Database Setup
Render will automatically:
- Create a PostgreSQL database
- Set the `DATABASE_URL` environment variable
- Run your application

### 5. Initial Setup
1. **Access your deployed application** at the provided URL
2. **Create the database tables** by visiting any page (Flask will auto-create them)
3. **Create an admin user** by running the following in Render's shell:
   ```bash
   python -c "
   from app import create_app, db, User
   app = create_app()
   with app.app_context():
       admin = User(username='admin', email='admin@example.com', is_admin=True)
       admin.set_password('admin123')
       db.session.add(admin)
       db.session.commit()
       print('Admin user created: admin / admin123')
   "
   ```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `your-secret-key-here` |
| `FLASK_ENV` | Environment mode | `production` |
| `DATABASE_URL` | Database connection | Auto-set by Render |
| `PORT` | Server port | Auto-set by Render |

## Automatic Deployments
✅ **Automatic deployments are enabled by default**
- Every push to your main branch will trigger a new deployment
- You can disable this in the Render dashboard if needed
- Deployments typically take 2-3 minutes

## Custom Domain (Optional)
1. In your Render service settings, go to "Custom Domains"
2. Add your domain name
3. Update your DNS records as instructed
4. SSL certificate will be automatically provisioned

## Monitoring & Logs
- **Logs:** Available in the Render dashboard
- **Metrics:** Basic metrics included in free tier
- **Health Checks:** Automatic health monitoring

## Troubleshooting

### Common Issues:
1. **Build Fails:** Check that all dependencies are in `requirements.txt`
2. **App Won't Start:** Verify the start command is `gunicorn app:app`
3. **Database Errors:** Ensure `DATABASE_URL` is set correctly
4. **Static Files:** Make sure static files are in the `static/` directory

### Getting Help:
- Render Documentation: [render.com/docs](https://render.com/docs)
- Render Community: [community.render.com](https://community.render.com)

## Security Notes
- ✅ HTTPS is automatically enabled
- ✅ Environment variables are secure
- ✅ Database credentials are managed by Render
- ⚠️ Change the default admin password after deployment
- ⚠️ Use a strong `SECRET_KEY` in production

## Cost
- **Free Tier:** 750 hours/month, 512MB RAM, 0.1 CPU
- **Paid Plans:** Start at $7/month for more resources
- **Database:** Free PostgreSQL database included

## Next Steps
1. Test your deployed application
2. Set up monitoring and alerts
3. Configure backup strategies
4. Consider upgrading to a paid plan for production use

---

**🎉 Congratulations! Your EMS Inventory System is now live on the web!**
