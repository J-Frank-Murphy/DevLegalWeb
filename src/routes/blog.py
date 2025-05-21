from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from src.models.blog import Post, Category, Tag, Comment
from src.models import db
from datetime import datetime
from slugify import slugify
import os

# Create blueprint
blog_bp = Blueprint('blog', __name__)

# Custom Pagination class for consistent pagination across all routes
class CustomPagination:
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        
    @property
    def pages(self):
        return max(1, self.total // self.per_page + (1 if self.total % self.per_page > 0 else 0))
        
    @property
    def has_prev(self):
        return self.page > 1
        
    @property
    def has_next(self):
        return self.page < self.pages
        
    @property
    def prev_num(self):
        return self.page - 1
        
    @property
    def next_num(self):
        return self.page + 1

# Helper function to create consistent pagination
def paginate_query(query, page, per_page):
    # Get total count before pagination
    total = query.count()
    
    # Get items for current page
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    
    # Return custom pagination object
    return CustomPagination(items, page, per_page, total)

# Helper function to paginate a list
def paginate_list(items, page, per_page):
    total = len(items)
    start = (page - 1) * per_page
    end = min(start + per_page, total)
    
    return CustomPagination(
        items[start:end],
        page,
        per_page,
        total
    )

@blog_bp.route('/')
def index():
    """Display blog index with latest posts"""
    page = request.args.get('page', 1, type=int)
    per_page = 6
    
    # Create query for published posts
    query = Post.query.filter_by(published=True).order_by(Post.created_at.desc())
    
    # Use custom pagination
    posts = paginate_query(query, page, per_page)
    
    return render_template('blog/index.html', 
                          posts=posts,
                          title="Blog")

@blog_bp.route('/post/<slug>')
def post(slug):
    """Display a single blog post"""
    post = Post.query.filter_by(slug=slug).first_or_404()
    
    # Increment view count
    post.views += 1
    db.session.commit()
    
    return render_template('blog/post.html', 
                          post=post,
                          title=post.title)

@blog_bp.route('/category/<slug>')
def category(slug):
    """Display posts by category"""
    category = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = 6
    
    # Create query for published posts in this category
    query = Post.query.filter_by(
        category_id=category.id, 
        published=True
    ).order_by(Post.created_at.desc())
    
    # Use custom pagination
    posts = paginate_query(query, page, per_page)
    
    return render_template('blog/category.html',
                          category=category,
                          posts=posts,
                          title=f"Category: {category.name}")

@blog_bp.route('/tag/<slug>')
def tag(slug):
    """Display posts by tag"""
    tag = Tag.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = 6
    
    # Filter published posts with this tag
    posts_with_tag = [post for post in tag.posts if post.published]
    
    # Use custom pagination for the filtered list
    posts = paginate_list(posts_with_tag, page, per_page)
    
    return render_template('blog/tag.html',
                          tag=tag,
                          posts=posts,
                          title=f"Tag: {tag.name}")

@blog_bp.route('/search')
def search():
    """Search blog posts"""
    query_text = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 6
    
    if not query_text:
        return render_template('blog/search.html',
                              posts=None,
                              query='',
                              title="Search")
    
    # Create query for published posts matching search
    query = Post.query.filter(
        Post.published == True,
        (Post.title.ilike(f'%{query_text}%') | Post.content.ilike(f'%{query_text}%'))
    ).order_by(Post.created_at.desc())
    
    # Use custom pagination
    posts = paginate_query(query, page, per_page)
    
    return render_template('blog/search.html',
                          posts=posts,
                          query=query_text,
                          title=f"Search: {query_text}")

@blog_bp.route('/post/<slug>/comment', methods=['POST'])
def add_comment(slug):
    """Add a comment to a blog post"""
    post = Post.query.filter_by(slug=slug).first_or_404()
    
    if not post.comments_enabled:
        flash('Comments are disabled for this post.', 'error')
        return redirect(url_for('blog.post', slug=slug))
    
    name = request.form.get('name')
    email = request.form.get('email')
    content = request.form.get('content')
    
    if not name or not email or not content:
        flash('All fields are required.', 'error')
        return redirect(url_for('blog.post', slug=slug))
    
    comment = Comment(
        post_id=post.id,
        name=name,
        email=email,
        content=content,
        approved=False  # Comments require approval
    )
    
    db.session.add(comment)
    db.session.commit()
    
    flash('Your comment has been submitted and is awaiting approval.', 'success')
    return redirect(url_for('blog.post', slug=slug))
