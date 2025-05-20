from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import re
from slugify import slugify
from src.models import db

# Many-to-many relationship between posts and tags
post_tags = Table(
    'post_tags',
    db.metadata,
    Column('post_id', Integer, ForeignKey('posts.id')),
    Column('tag_id', Integer, ForeignKey('tags.id')),
    extend_existing=True
)

class Post(db.Model):
    __tablename__ = 'posts'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    excerpt = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    featured_image = Column(String(255), nullable=True)
    published = Column(Boolean, default=False)
    comments_enabled = Column(Boolean, default=True)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship('Category', back_populates='posts')
    tags = relationship('Tag', secondary=post_tags, back_populates='posts')
    comments = relationship('Comment', back_populates='post', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = slugify(self.title)
    
    def __repr__(self):
        return f'<Post {self.title}>'
    
    @property
    def html_content(self):
        from src.utils import markdown_to_html
        return markdown_to_html(self.content)
    
    @property
    def reading_time(self):
        # Calculate reading time based on content length
        word_count = len(re.findall(r'\w+', self.content))
        minutes = word_count // 200  # Assuming 200 words per minute reading speed
        return max(1, minutes)  # Minimum 1 minute

class Category(db.Model):
    __tablename__ = 'categories'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Relationships
    posts = relationship('Post', back_populates='category')
    
    def __init__(self, **kwargs):
        super(Category, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = slugify(self.name)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    @property
    def post_count(self):
        return Post.query.filter_by(category_id=self.id, published=True).count()

class Tag(db.Model):
    __tablename__ = 'tags'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    
    # Relationships
    posts = relationship('Post', secondary=post_tags, back_populates='tags')
    
    def __init__(self, **kwargs):
        super(Tag, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = slugify(self.name)
    
    def __repr__(self):
        return f'<Tag {self.name}>'
    
    @property
    def post_count(self):
        return len([post for post in self.posts if post.published])

class Comment(db.Model):
    __tablename__ = 'comments'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship('Post', back_populates='comments')
    
    def __repr__(self):
        return f'<Comment by {self.name} on {self.post.title}>'
