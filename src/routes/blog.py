from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from src.models.blog import Post, Category, Tag, Comment
from src.models import db
from datetime import datetime
from slugify import slugify
import os

# Create blueprint
blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/')
def index():
    """Display blog index with latest posts"""
    page = request.args.get('page', 1, type=int)
    per_page = 6
    
    posts = Post.query.filter_by(published=True).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
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
    
    posts = Post.query.filter_by(
        category_id=category.id, 
        published=True
    ).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
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
    total = len(posts_with_tag)
    
    # Manual pagination since we're working with a filtered list
    start = (page - 1) * per_page
    end = min(start + per_page, total)
    
    class Pagination:
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
    
    paginated_posts = Pagination(
        posts_with_tag[start:end],
        page,
        per_page,
        total
    )
    
    return render_template('blog/tag.html',
                          tag=tag,
                          posts=paginated_posts,
                          title=f"Tag: {tag.name}")

@blog_bp.route('/search')
def search():
    """Search blog posts"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 6
    
    if not query:
        return render_template('blog/search.html',
                              posts=None,
                              query='',
                              title="Search")
    
    # Search in title and content
    posts = Post.query.filter(
        Post.published == True,
        (Post.title.ilike(f'%{query}%') | Post.content.ilike(f'%{query}%'))
    ).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    return render_template('blog/search.html',
                          posts=posts,
                          query=query,
                          title=f"Search: {query}")

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
