from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from src.csrf_fix import init_csrf
import os

# Initialize extensions
login_manager = LoginManager()
login_manager.login_view = 'admin.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Import models
from src.models import db
from src.models.user import User
from src.routes.news_links import news_links_bp
from src.models import user, blog, news_link

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config=None):
    """Application factory pattern for Flask app"""
    app = Flask(__name__)
    
    # Load configuration
    configure_app(app, config)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)
    init_csrf(app)
    
    # Register blueprints
    register_blueprints(app) 
    
    # Register main routes
    from src.routes.main import register_main_routes
    register_main_routes(app)   
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    register_context_processors(app)
    
    return app

def configure_app(app, config=None):
    """Configure the Flask application"""
    # Default configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    
    # Database configuration
    # Check for DATABASE_URL (Render provides this for PostgreSQL)
    if os.environ.get('DATABASE_URL'):
        # Render provides PostgreSQL URL in format: postgres://user:pass@host:port/db
        # SQLAlchemy requires: postgresql://user:pass@host:port/db
        db_url = os.environ.get('DATABASE_URL')
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    # Check for USE_SQLITE flag
    elif os.environ.get('USE_SQLITE'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dev_legal.db'
    # Otherwise use MySQL with environment variables or defaults
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.environ.get('DB_USERNAME', 'root')}:{os.environ.get('DB_PASSWORD', 'password')}@{os.environ.get('DB_HOST', 'localhost')}:{os.environ.get('DB_PORT', '3306')}/{os.environ.get('DB_NAME', 'mydb')}"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Upload configuration
    if os.path.exists('/opt/render/persistent-uploads'):
        # Use persistent disk on Render
        app.config['UPLOAD_FOLDER'] = '/opt/render/persistent-uploads'
        app.config['UPLOADS_URL_PATH'] = '/uploads'  # URL path for serving files
        
        # Create a route to serve files from persistent disk
        @app.route('/uploads/<path:filename>')
        def uploaded_file(filename):
            return send_from_directory('/opt/render/persistent-uploads', filename)
            
        # Handle legacy paths that might be in the database
        @app.route('/static/uploads/<path:filename>')
        def legacy_uploaded_file(filename):
            # First try to serve from persistent disk
            if os.path.exists(os.path.join('/opt/render/persistent-uploads', filename)):
                return send_from_directory('/opt/render/persistent-uploads', filename)
            # Fall back to static folder
            return send_from_directory(os.path.join(app.static_folder, 'uploads'), filename)
    else:
        # Local development - use static folder
        app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
        app.config['UPLOADS_URL_PATH'] = '/static/uploads'  # URL path for static folder
    
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Override with any provided config
    if config:
        app.config.update(config)

def register_blueprints(app):
    """Register Flask blueprints"""
    from src.routes.blog import blog_bp
    from src.routes.api import api_bp
    from src.routes.admin import admin_bp
    
    app.register_blueprint(blog_bp, url_prefix='/blog')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(news_links_bp)

def register_error_handlers(app):
    """Register error handlers"""
    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('500.html'), 500

def register_context_processors(app):
    """Register context processors"""
    @app.context_processor
    def inject_categories_and_tags():
        from src.models.blog import Category, Tag
        from datetime import datetime
        
        categories = Category.query.all()
        tags = Tag.query.all()
        return dict(categories=categories, tags=tags, now=datetime.now())
