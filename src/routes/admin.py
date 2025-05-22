from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from src.models.user import User
from src.models.blog import Post, Category, Tag, Comment
from src.models import db
import os
from datetime import datetime
import uuid
import re
import traceback

# Create blueprint
admin_bp = Blueprint('admin', __name__)

def allowed_file(filename):
    """Check if a filename has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_image(file):
    """Save an uploaded image and return the path"""
    current_app.logger.info("=== Starting save_image function ===")
    current_app.logger.info(f"File: {file.filename if file else 'None'}")
    
    if file and allowed_file(file.filename):
        # Generate a secure filename with a unique identifier
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        current_app.logger.info(f"Generated unique filename: {unique_filename}")
        
        # Use the app's configured upload folder (which will be the persistent disk on Render)
        uploads_dir = current_app.config['UPLOAD_FOLDER']
        current_app.logger.info(f"Upload directory: {uploads_dir}")
        current_app.logger.info(f"Directory exists: {os.path.exists(uploads_dir)}")
        
        os.makedirs(uploads_dir, exist_ok=True)
        current_app.logger.info(f"Directory created/verified")
        
        # Save the file to the configured upload folder
        file_path = os.path.join(uploads_dir, unique_filename)
        current_app.logger.info(f"Full file path: {file_path}")
        
        try:
            file.save(file_path)
            current_app.logger.info(f"File saved successfully")
            current_app.logger.info(f"File exists after save: {os.path.exists(file_path)}")
        except Exception as e:
            current_app.logger.error(f"Error saving file: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            return None
        
        # Return the relative path using the configured URL path
        relative_path = f"{current_app.config['UPLOADS_URL_PATH'].strip('/')}/{unique_filename}"
        current_app.logger.info(f"Returning relative path: {relative_path}")
        return relative_path
    
    current_app.logger.error(f"File validation failed: {file.filename if file else 'None'}")
    return None

@admin_bp.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    """Handle image uploads from Quill editor"""
    current_app.logger.info("=== Starting Quill image upload ===")
    current_app.logger.info(f"Request files: {request.files}")
    
    if 'file' not in request.files:
        current_app.logger.error("No file part in request")
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    current_app.logger.info(f"File name: {file.filename}")
    
    if file.filename == '':
        current_app.logger.error("No selected file")
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        current_app.logger.info("File is allowed, saving...")
        file_path = save_image(file)
        if file_path:
            # Return the URL for the uploaded image in Quill format
            result_url = url_for('static', filename=file_path) if file_path.startswith('uploads/') else file_path
            current_app.logger.info(f"Returning URL: {result_url}")
            
            return jsonify({
                'success': True,
                'url': result_url
            })
    
    current_app.logger.error("Invalid file type or save failed")
    return jsonify({'error': 'Invalid file type'}), 400

# New route for handling content image uploads
@admin_bp.route('/upload-content-image', methods=['POST'])
@login_required
def upload_content_image():
    """Handle content image uploads for post content"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        file_path = save_image(file)
        if file_path:
            # Return both the full URL and the filename for different insertion formats
            return jsonify({
                'success': True,
                'url': url_for('static', filename=file_path, _external=True),
                'relative_url': url_for('static', filename=file_path),
                'filename': os.path.basename(file_path)
            })
    
    return jsonify({'error': 'Invalid file type'}), 400


# Rest of your admin.py file...
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html', title="Admin Login")

@admin_bp.route('/logout')
@login_required
def logout():
    """Admin logout"""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@login_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    post_count = Post.query.count()
    published_count = Post.query.filter_by(published=True).count()
    draft_count = post_count - published_count
    category_count = Category.query.count()
    tag_count = Tag.query.count()
    comment_count = Comment.query.count()
    pending_comments = Comment.query.filter_by(approved=False).count()
    
    # Get recent posts
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    
    # Get recent comments
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
    
    return render_template('admin/index.html',
                          title="Admin Dashboard",
                          post_count=post_count,
                          published_count=published_count,
                          draft_count=draft_count,
                          category_count=category_count,
                          tag_count=tag_count,
                          comment_count=comment_count,
                          pending_comments=pending_comments,
                          recent_posts=recent_posts,
                          recent_comments=recent_comments)

@admin_bp.route('/posts')
@login_required
def posts():
    """Manage blog posts"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/posts.html', title="Manage Posts", posts=posts)

@admin_bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    """Create a new blog post"""
    categories = Category.query.all()
    tags = Tag.query.all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        excerpt = request.form.get('excerpt')
        content = request.form.get('content')
        content_format = request.form.get('content_format', 'html')  # Default to HTML if not specified
        category_id = request.form.get('category_id')
        tag_ids = request.form.getlist('tags')
        featured_image_url = request.form.get('featured_image_url')
        published = 'published' in request.form
        comments_enabled = 'comments_enabled' in request.form
        post_date = request.form.get('post_date')
        
        # Validate required fields
        if not title or not content or not category_id:
            flash('Title, content, and category are required.', 'error')
            return render_template('admin/post_form.html', title="New Post", categories=categories, tags=tags)
        
        # Handle featured image (file upload takes precedence over URL)
        featured_image = featured_image_url
        if 'featured_image_file' in request.files:
            file = request.files['featured_image_file']
            if file and file.filename:
                file_path = save_image(file)
                if file_path:
                    featured_image = file_path
        
        # Create new post
        post = Post(
            title=title,
            slug=slug,
            excerpt=excerpt,
            content=content,
            content_format=content_format,  # Save the content format
            category_id=category_id,
            featured_image=featured_image,
            published=published,
            comments_enabled=comments_enabled
        )
        
        # Set custom created_at date if provided
        if post_date:
            try:
                post.created_at = datetime.strptime(post_date, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Invalid date format. Using current date instead.', 'warning')
        
        # Add tags
        for tag_id in tag_ids:
            tag = Tag.query.get(tag_id)
            if tag:
                post.tags.append(tag)
        
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('admin.posts'))
    
    return render_template('admin/post_form.html', title="New Post", categories=categories, tags=tags)

@admin_bp.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """Edit an existing blog post"""
    post = Post.query.get_or_404(post_id)
    categories = Category.query.all()
    tags = Tag.query.all()
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.slug = request.form.get('slug')
        post.excerpt = request.form.get('excerpt')
        post.content = request.form.get('content')
        post.content_format = request.form.get('content_format', 'html')  # Update content format
        post.category_id = request.form.get('category_id')
        featured_image_url = request.form.get('featured_image_url')
        post.published = 'published' in request.form
        post.comments_enabled = 'comments_enabled' in request.form
        post_date = request.form.get('post_date')
        
        # Update created_at date if provided
        if post_date:
            try:
                post.created_at = datetime.strptime(post_date, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Invalid date format. Original date retained.', 'warning')
        
        # Handle featured image (file upload takes precedence over URL)
        if 'featured_image_file' in request.files:
            file = request.files['featured_image_file']
            if file and file.filename:
                file_path = save_image(file)
                if file_path:
                    post.featured_image = file_path  # If a new file is uploaded, it takes precedence over the URL
            else:
                # If file upload fails, use the URL
                post.featured_image = featured_image_url
        else:
            # If no file is uploaded, use the URL
            post.featured_image = featured_image_url
        
        # Update tags
        post.tags = []
        tag_ids = request.form.getlist('tags')
        for tag_id in tag_ids:
            tag = Tag.query.get(tag_id)
            if tag:
                post.tags.append(tag)
        
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin.posts'))
    
    return render_template('admin/post_form.html', title="Edit Post", post=post, categories=categories, tags=tags)

@admin_bp.route('/post/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    """Delete a blog post"""
    post = Post.query.get_or_404(post_id)
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin.posts'))

@admin_bp.route('/categories')
@login_required
def categories():
    """Manage categories"""
    categories = Category.query.all()
    return render_template('admin/categories.html', title="Manage Categories", categories=categories)

@admin_bp.route('/category/new', methods=['GET', 'POST'])
@login_required
def new_category():
    """Create a new category"""
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        description = request.form.get('description')
        
        if not name:
            flash('Category name is required.', 'error')
            return render_template('admin/category_form.html', title="New Category")
        
        category = Category(name=name, slug=slug, description=description)
        db.session.add(category)
        db.session.commit()
        
        flash('Category created successfully!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html', title="New Category")

@admin_bp.route('/category/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """Edit an existing category"""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.slug = request.form.get('slug')
        category.description = request.form.get('description')
        
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html', title="Edit Category", category=category)

@admin_bp.route('/category/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    """Delete a category"""
    category = Category.query.get_or_404(category_id)
    
    # Check if category has posts
    if category.posts:
        flash('Cannot delete category with associated posts.', 'error')
        return redirect(url_for('admin.categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/tags')
@login_required
def tags():
    """Manage tags"""
    tags = Tag.query.all()
    return render_template('admin/tags.html', title="Manage Tags", tags=tags)

@admin_bp.route('/tag/new', methods=['GET', 'POST'])
@login_required
def new_tag():
    """Create a new tag"""
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        
        if not name:
            flash('Tag name is required.', 'error')
            return render_template('admin/tag_form.html', title="New Tag")
        
        tag = Tag(name=name, slug=slug)
        db.session.add(tag)
        db.session.commit()
        
        flash('Tag created successfully!', 'success')
        return redirect(url_for('admin.tags'))
    
    return render_template('admin/tag_form.html', title="New Tag")

@admin_bp.route('/tag/edit/<int:tag_id>', methods=['GET', 'POST'])
@login_required
def edit_tag(tag_id):
    """Edit an existing tag"""
    tag = Tag.query.get_or_404(tag_id)
    
    if request.method == 'POST':
        tag.name = request.form.get('name')
        tag.slug = request.form.get('slug')
        
        db.session.commit()
        flash('Tag updated successfully!', 'success')
        return redirect(url_for('admin.tags'))
    
    return render_template('admin/tag_form.html', title="Edit Tag", tag=tag)

@admin_bp.route('/tag/delete/<int:tag_id>', methods=['POST'])
@login_required
def delete_tag(tag_id):
    """Delete a tag"""
    tag = Tag.query.get_or_404(tag_id)
    
    db.session.delete(tag)
    db.session.commit()
    
    flash('Tag deleted successfully!', 'success')
    return redirect(url_for('admin.tags'))

@admin_bp.route('/comments')
@login_required
def comments():
    """Manage comments"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    comments = Comment.query.order_by(Comment.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/comments.html', title="Manage Comments", comments=comments)

@admin_bp.route('/comment/approve/<int:comment_id>', methods=['POST'])
@login_required
def approve_comment(comment_id):
    """Approve a comment"""
    comment = Comment.query.get_or_404(comment_id)
    
    comment.approved = True
    db.session.commit()
    
    flash('Comment approved successfully!', 'success')
    return redirect(url_for('admin.comments'))

@admin_bp.route('/comment/delete/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """Delete a comment"""
    comment = Comment.query.get_or_404(comment_id)
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comment deleted successfully!', 'success')
    return redirect(url_for('admin.comments'))
