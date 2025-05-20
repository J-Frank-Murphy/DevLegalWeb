# Render Deployment Guide for Dev Legal Website (Updated)

This guide provides step-by-step instructions for deploying the Dev Legal website to Render.com with a custom domain. This updated version includes the CSRF fix for the admin interface.

## Prerequisites

1. A GitHub account with your Dev Legal website code repository
2. A Render.com account (free tier is sufficient)
3. Your domain name (if you want to use a custom domain)

## Step 1: Prepare Your Repository

Ensure your repository includes:
- All application code in the correct directory structure
- A requirements.txt file with all dependencies
- The CSRF fix implementation (csrf_fix.py and updated __init__.py)
- A Procfile with the command: `gunicorn "src:create_app()"`

## Step 2: Create a New Web Service on Render

1. Log in to your Render dashboard: https://dashboard.render.com/
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: Choose a name for your service (e.g., "dev-legal-website")
   - **Environment**: Select "Python 3"
   - **Region**: Choose a region close to your target audience
   - **Branch**: Select your main branch (usually "main" or "master")
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn "src:create_app()"`

## Step 3: Configure Environment Variables

Add the following environment variables:
- **SECRET_KEY**: Generate a strong random string (e.g., use a password generator)
- **DATABASE_URL**: This will be automatically set if you create a Render PostgreSQL database

Optional variables:
- **USE_SQLITE**: Set to "true" if you want to use SQLite instead of PostgreSQL

## Step 4: Initialize the Database

After deployment completes, go to the "Shell" tab in your Render dashboard and run:

```bash
python
>>> from src import create_app
>>> app = create_app()
>>> from src.models import db
>>> with app.app_context():
...     db.create_all()
...     from src.models.user import User
...     from werkzeug.security import generate_password_hash
...     user = User(username="admin", password_hash=generate_password_hash("devlegal2025"), is_admin=True)
...     db.session.add(user)
...     db.session.commit()
>>> exit()
```

Note: Make sure to press Enter twice after the last line in the indented block to execute it.

## Step 5: Set Up a Custom Domain (Optional)

1. Go to your web service settings in Render
2. Click on "Custom Domain"
3. Add your domain and follow the instructions to configure DNS settings

## Step 6: Verify Deployment

1. Visit your Render URL (e.g., https://dev-legal-website.onrender.com)
2. Test the admin interface by navigating to /admin
3. Log in with username "admin" and password "devlegal2025"

## Troubleshooting

If you encounter issues with the admin interface:

1. Check Render logs for specific error messages
2. Verify that the CSRF fix is properly implemented:
   - Ensure csrf_fix.py exists in the src directory
   - Confirm that __init__.py imports and initializes CSRF protection
3. Make sure the database is properly initialized with an admin user

## Maintenance

To update your website:
1. Push changes to your GitHub repository
2. Render will automatically deploy the updates

For database schema changes:
1. Use the Render shell to apply migrations or update the schema
2. Or implement Flask-Migrate for more structured migrations
