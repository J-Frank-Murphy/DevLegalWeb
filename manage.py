from flask.cli import FlaskGroup
from src import create_app
from src.models import db
from src.models.user import User
from werkzeug.security import generate_password_hash
import os

app = create_app()
cli = FlaskGroup(create_app=lambda: app)

@cli.command("create-admin")
def create_admin():
    """Create an admin user"""
    username = os.environ.get('ADMIN_USERNAME', 'admin')
    password = os.environ.get('ADMIN_PASSWORD', 'devlegal2025')
    
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

@cli.command("init-db")
def init_db():
    """Initialize the database"""
    db.create_all()
    print("Database tables created")

if __name__ == '__main__':
    cli()
