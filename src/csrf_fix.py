from flask_wtf.csrf import CSRFProtect

# Initialize CSRF protection
csrf = CSRFProtect()

def init_csrf(app):
    """Initialize CSRF protection"""
    csrf.init_app(app)
