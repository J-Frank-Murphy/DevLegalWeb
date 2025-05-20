import markdown
import bleach
from bleach.sanitizer import ALLOWED_TAGS, ALLOWED_ATTRIBUTES

def allowed_file(filename):
    """Check if a filename has an allowed extension"""
    from flask import current_app
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def sanitize_html(html_content):
    """Sanitize HTML content to prevent XSS attacks"""
    # Add additional tags and attributes for rich text
    allowed_tags = list(ALLOWED_TAGS) + [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
        'p', 'br', 'hr', 'img', 'pre', 'code', 
        'blockquote', 'div', 'span', 'ul', 'ol', 
        'li', 'table', 'thead', 'tbody', 'tr', 
        'th', 'td'
    ]
    
    allowed_attrs = dict(ALLOWED_ATTRIBUTES)
    allowed_attrs.update({
        'img': ['src', 'alt', 'title', 'width', 'height', 'class'],
        'a': ['href', 'title', 'target', 'rel', 'class'],
        'div': ['class', 'id'],
        'span': ['class', 'id'],
        'code': ['class'],
        'pre': ['class'],
        'table': ['class', 'border'],
        'th': ['scope', 'colspan', 'rowspan'],
        'td': ['colspan', 'rowspan']
    })
    
    return bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attrs)

def markdown_to_html(md_content):
    """Convert markdown to HTML and sanitize it"""
    # Convert markdown to HTML
    html = markdown.markdown(md_content, extensions=['extra', 'codehilite', 'tables'])
    
    # Sanitize the HTML
    return sanitize_html(html)
