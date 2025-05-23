from flask import Blueprint, jsonify, request, render_template, current_app
from src.models.news_link import NewsLink
from src.models.blog import Post, Category
from src import db
from datetime import datetime
from flask_login import login_required
import requests
import json
import os
import re
from slugify import slugify
import random
import string

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
    try:
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
            except ValueError as e:
                return jsonify({'error': f'Invalid date format for date_of_article: {e}'}), 400
        
        if 'date_fetched' in data:
            try:
                if data['date_fetched']:
                    link.date_fetched = datetime.fromisoformat(data['date_fetched']).date()
                else:
                    link.date_fetched = None
            except ValueError as e:
                return jsonify({'error': f'Invalid date format for date_fetched: {e}'}), 400
        
        if 'focus_of_article' in data:
            link.focus_of_article = data['focus_of_article']
        
        if 'article_written' in data:
            link.article_written = bool(data['article_written'])
        
        db.session.commit()
        return jsonify(link.to_dict())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating link: {e}")
        return jsonify({'error': str(e)}), 500

@news_links_bp.route('/api/links/<int:link_id>', methods=['DELETE'])
@login_required
def delete_link(link_id):
    """Delete a news link"""
    try:
        link = NewsLink.query.get_or_404(link_id)
        db.session.delete(link)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting link: {e}")
        return jsonify({'error': str(e)}), 500

@news_links_bp.route('/api/links', methods=['POST'])
@login_required
def create_link():
    """Create a new news link"""
    try:
        data = request.json
        
        if not data.get('url'):
            return jsonify({'error': 'URL is required'}), 400
        
        date_of_article = None
        if data.get('date_of_article'):
            try:
                date_of_article = datetime.fromisoformat(data['date_of_article']).date()
            except ValueError as e:
                current_app.logger.error(f"Date conversion error: {e}")
                return jsonify({'error': f'Invalid date format for date_of_article: {e}'}), 400
        
        date_fetched = datetime.now().date()
        if data.get('date_fetched'):
            try:
                date_fetched = datetime.fromisoformat(data['date_fetched']).date()
            except ValueError as e:
                current_app.logger.error(f"Date conversion error: {e}")
                return jsonify({'error': f'Invalid date format for date_fetched: {e}'}), 400
        
        article_written = bool(data.get('article_written', False))
        
        link = NewsLink(
            url=data['url'],
            date_of_article=date_of_article,
            date_fetched=date_fetched,
            focus_of_article=data.get('focus_of_article'),
            article_written=article_written
        )
        
        db.session.add(link)
        db.session.commit()
        
        return jsonify(link.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating link: {e}")
        return jsonify({'error': str(e)}), 500

@news_links_bp.route('/api/generate-article', methods=['POST'])
@login_required
def generate_article():
    """Generate an article using OpenAI API and create a post"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('url'):
            return jsonify({'error': 'URL is required'}), 400
        if not data.get('focus_of_article'):
            return jsonify({'error': 'Focus of article is required'}), 400
        if not data.get('link_id'):
            return jsonify({'error': 'Link ID is required'}), 400
        
        # Get the link
        link = NewsLink.query.get(data['link_id'])
        if not link:
            return jsonify({'error': 'Link not found'}), 404
        
        # Get OpenAI API key from environment variable
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'error': 'OpenAI API key not found in environment variables'}), 500
        
        # Prepare the OpenAI API request
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Construct the user prompt
        user_prompt = f"Write a short blog post commenting on this news story: {data['url']}. The focus of the article should be {data['focus_of_article']}. Compose the article in markdown format, and give it a title and a one sentence summary. If you link to the news story in the article, then do so in a way such that the link opens in a new tab. Return your response as a JSON object with the structure below. Do not return any other text or data other than the JSON object.\n\n{{\n\"title\": string,\n\"excerpt\": string,\n\"content\": string\n}}"
        
        # Construct the system prompt
        system_prompt = "You are a helpful assistant that writes commentary on issues relating to technology, the law, intellectual property, and open source licensing and compliance"
        
        # Prepare the request payload
        payload = {
            "model": "o3",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        # Make the API request
        current_app.logger.info(f"Sending request to OpenAI API: {payload}")
        response = requests.post(url, headers=headers, json=payload)
        
        # Check if the request was successful
        if response.status_code != 200:
            current_app.logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return jsonify({'error': f'OpenAI API error: {response.status_code} - {response.text}'}), 500
        
        # Parse the response
        response_data = response.json()
        current_app.logger.info(f"Received response from OpenAI API: {response_data}")
        
        # Extract the content from the response
        try:
            content = response_data['choices'][0]['message']['content']
            # Parse the JSON from the content
            article_data = json.loads(content)
            
            # Validate the article data
            if not article_data.get('title') or not article_data.get('excerpt') or not article_data.get('content'):
                return jsonify({'error': 'Invalid article data received from OpenAI'}), 500
            
            # Get the Drafts category
            drafts_category = Category.query.filter_by(name='Drafts').first()
            if not drafts_category:
                return jsonify({'error': 'Drafts category not found'}), 500
            
            # Generate a slug from the title
            base_slug = slugify(article_data['title'])
            
            # Check if the slug already exists
            existing_post = Post.query.filter_by(slug=base_slug).first()
            if existing_post:
                # Add a random string to make the slug unique
                random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                slug = f"{base_slug}-{random_string}"
            else:
                slug = base_slug
            
            # Create a new post
            post = Post(
                title=article_data['title'],
                slug=slug,
                content=article_data['content'],
                excerpt=article_data['excerpt'],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                published=False,
                comments_enabled=False,
                category_id=drafts_category.id,
                content_format='markdown'
            )
            
            # Add the post to the database
            db.session.add(post)
            
            # Update the link to mark article as written
            link.article_written = True
            
            # Commit the changes
            db.session.commit()
            
            # Return the post data
            return jsonify({
                'success': True,
                'post_id': post.id,
                'title': post.title,
                'slug': post.slug
            })
            
        except (json.JSONDecodeError, KeyError) as e:
            current_app.logger.error(f"Error parsing OpenAI response: {e}")
            return jsonify({'error': f'Error parsing OpenAI response: {e}'}), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error generating article: {e}")
        return jsonify({'error': str(e)}), 500
