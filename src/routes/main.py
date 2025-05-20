from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from src.models.blog import Post, Category, Tag, Comment
from datetime import datetime
from src.utils import markdown_to_html

# Create main routes (not in a blueprint)
# These will be registered directly with the app

def register_main_routes(app):
    """Register main routes directly with the app"""
    
    @app.route('/')
    def index():
        """Homepage route"""
        # Get latest blog posts for homepage
        latest_posts = Post.query.filter_by(published=True).order_by(
            Post.created_at.desc()
        ).limit(3).all()
        
        return render_template('index.html', 
                              latest_posts=latest_posts,
                              now=datetime.now())
    
    @app.route('/contact', methods=['POST'])
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
    
    @app.route('/subscribe', methods=['POST'])
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
