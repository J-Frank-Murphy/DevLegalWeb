from flask import Blueprint, jsonify, request, render_template
from src.models.news_link import NewsLink
from src import db
from datetime import datetime
from flask_login import login_required

news_links_bp = Blueprint('news_links', __name__, url_prefix='/admin/news-links')

@news_links_bp.route('/')
@login_required
def index():
    """Render the admin interface for news links"""
    return render_template('admin/news_links/index.html')

@news_links_bp.route('/api/links', methods=['GET'])
@login_required
def get_links():
    """Get all news links ordered by date_fetched"""
    links = NewsLink.query.order_by(NewsLink.date_fetched.desc()).all()
    return jsonify([link.to_dict() for link in links])

@news_links_bp.route('/api/links/<int:link_id>', methods=['PUT'])
@login_required
def update_link(link_id):
    """Update a news link"""
    link = NewsLink.query.get_or_404(link_id)
    data = request.json
    
    if 'url' in data:
        link.url = data['url']
    
    if 'date_of_article' in data:
        try:
            if data['date_of_article']:
                link.date_of_article = datetime.fromisoformat(data['date_of_article']).date()
            else:
                link.date_of_article = None
        except ValueError:
            return jsonify({'error': 'Invalid date format for date_of_article'}), 400
    
    if 'date_fetched' in data:
        try:
            if data['date_fetched']:
                link.date_fetched = datetime.fromisoformat(data['date_fetched']).date()
            else:
                link.date_fetched = None
        except ValueError:
            return jsonify({'error': 'Invalid date format for date_fetched'}), 400
    
    if 'article_written' in data:
        link.article_written = bool(data['article_written'])
        
    if 'focus_of_article' in data:
        link.focus_of_article = data['focus_of_article']
    
    db.session.commit()
    return jsonify(link.to_dict())

@news_links_bp.route('/api/links/<int:link_id>', methods=['DELETE'])
@login_required
def delete_link(link_id):
    """Delete a news link"""
    link = NewsLink.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()
    return jsonify({'success': True})

@news_links_bp.route('/api/links', methods=['POST'])
@login_required
def create_link():
    """Create a new news link"""
    data = request.json
    
    if not data.get('url'):
        return jsonify({'error': 'URL is required'}), 400
    
    date_of_article = None
    if data.get('date_of_article'):
        try:
            date_of_article = datetime.fromisoformat(data['date_of_article']).date()
        except ValueError:
            return jsonify({'error': 'Invalid date format for date_of_article'}), 400
    
    date_fetched = datetime.now().date()
    if data.get('date_fetched'):
        try:
            date_fetched = datetime.fromisoformat(data['date_fetched']).date()
        except ValueError:
            return jsonify({'error': 'Invalid date format for date_fetched'}), 400
    
    article_written = bool(data.get('article_written', False))
    focus_of_article = data.get('focus_of_article', None)
    
    link = NewsLink(
        url=data['url'],
        date_of_article=date_of_article,
        date_fetched=date_fetched,
        article_written=article_written,
        focus_of_article=focus_of_article
    )
    
    db.session.add(link)
    db.session.commit()
    return jsonify(link.to_dict()), 201
