from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from src import create_app
from src.models import db
from src.models.user import User
from werkzeug.security import generate_password_hash
import os

# Create a minimal Flask app for migrations
app = create_app()

# Initialize migrations directory
@app.cli.command("init")
def init():
    """Initialize migrations directory"""
    from flask_migrate import init as migrate_init
    migrate_init()
    print("Migrations directory initialized")

# Create a migration
@app.cli.command("migrate")
def migrate():
    """Create a migration"""
    from flask_migrate import migrate as migrate_migrate
    migrate_migrate(message="Initial migration")
    print("Migration created")

# Apply migrations
@app.cli.command("upgrade")
def upgrade():
    """Apply migrations"""
    from flask_migrate import upgrade as migrate_upgrade
    migrate_upgrade()
    print("Migrations applied")

# Create admin user
@app.cli.command("create-admin")
def create_admin():
    """Create admin user"""
    username = os.environ.get('ADMIN_USERNAME', 'admin')
    password = os.environ.get('ADMIN_PASSWORD', 'devlegal2025')
    
    with app.app_context():
        # Check if user already exists
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"Admin user '{username}' already exists")
            return
        
        # Create new admin user
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            is_admin=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        print(f"Admin user '{username}' created successfully")
