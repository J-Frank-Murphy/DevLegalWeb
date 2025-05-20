from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from src.models.blog import Post, Category, Tag, Comment
from datetime import datetime
from src.utils import markdown_to_html

# Create a blueprint for main routes instead of registering directly with app
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage route"""
    # Get latest blog posts for homepage
    latest_posts = Post.query.filter_by(published=True).order_by(
        Post.created_at.desc()
    ).limit(3).all()
    
    return render_template('index.html', 
                          latest_posts=latest_posts,
                          now=datetime.now())

@main_bp.route('/contact', methods=['POST'])
def contact():
    """Contact form submission"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Here you would typically send an email or save to database
        # For now, we'll just return a success message
        return jsonify({
            'success': True, 
            'message': 'Message received! We will get back to you soon.'
        })

@main_bp.route('/subscribe', methods=['POST'])
def subscribe():
    """Newsletter subscription"""
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        
        # Here you would typically add to a newsletter service or database
        # For now, we'll just return a success message
        return jsonify({
            'success': True, 
            'message': 'Successfully subscribed to newsletter!'
        })

# Function to register the blueprint
def register_main_routes(app):
    """Register main routes as a blueprint"""
    app.register_blueprint(main_bp)
