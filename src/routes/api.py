from flask import Blueprint, request, jsonify, url_for, current_app
from src.models.blog import Post, Category, Tag, Comment
from src.models import db
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid

# Create blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/contact', methods=['POST'])
def contact():
    """Handle contact form submissions"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Validate inputs
        if not name or not email or not message:
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Here you would typically send an email or save to database
        # For demo purposes, we'll just return success
        return jsonify({
            'success': True,
            'message': 'Your message has been received. We will get back to you soon.'
        })

@api_bp.route('/subscribe', methods=['POST'])
def subscribe():
    """Handle newsletter subscriptions"""
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        role = request.form.get('role', '')
        
        # Validate email
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'})
        
        # Here you would typically add to a newsletter service or database
        # For demo purposes, we'll just return success
        return jsonify({
            'success': True,
            'message': 'Thank you for subscribing to our newsletter!'
        })

@api_bp.route('/upload-image', methods=['POST'])
def upload_image():
    """Handle image uploads for blog posts"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Save file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Return the URL to the uploaded file
        file_url = url_for('static', filename=f'uploads/{filename}', _external=True)
        return jsonify({
            'success': True,
            'file_url': file_url,
            'message': 'File uploaded successfully'
        })
    
    return jsonify({'success': False, 'message': 'File type not allowed'})

@api_bp.route('/toggle-comment', methods=['POST'])
def toggle_comment():
    """Toggle comments on/off for a post"""
    post_id = request.form.get('post_id')
    
    if not post_id:
        return jsonify({'success': False, 'message': 'Post ID is required'})
    
    post = Post.query.get_or_404(post_id)
    
    # Toggle comments
    post.comments_enabled = not post.comments_enabled
    db.session.commit()
    
    return jsonify({
        'success': True,
        'comments_enabled': post.comments_enabled,
        'message': f'Comments {"enabled" if post.comments_enabled else "disabled"} successfully'
    })
