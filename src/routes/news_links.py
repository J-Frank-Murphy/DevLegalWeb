from flask import Blueprint, jsonify, request, render_template, current_app
from src.models.news_link import NewsLink
from src.models.blog import Post, Category
from src import db
from datetime import datetime, timedelta
from flask_login import login_required
import requests
import json
import os
import re
from slugify import slugify
import random
import string
import urllib.parse

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
    
    link = NewsLink(
        url=data['url'],
        date_of_article=date_of_article,
        date_fetched=date_fetched,
        article_written=article_written
    )
    
    db.session.add(link)
    db.session.commit()
    
    return jsonify(link.to_dict()), 201

@news_links_bp.route('/api/fetch-perplexity', methods=['POST'])
@login_required
def fetch_perplexity_links():
    """Fetch links from Perplexity AI based on selected topic"""
    try:
        # Get API key from environment
        api_key = os.environ.get('PERPLEXITY_API_KEY')
        if not api_key:
            current_app.logger.error("Perplexity API key not found in environment variables")
            return jsonify({'success': False, 'error': 'API key not found'}), 500
        
        # Get selected topic from request
        data = request.json
        topic = data.get('topic', 'intellectual property issues')  # Default if not provided
        
        # Validate topic
        valid_topics = [
            'intellectual property issues',
            'open source software licensing and compliance',
            'data privacy',
            'law, policy, and regulation about technology',
            'lawsuits or regulatory actions involving technology companies'
        ]
        
        if topic not in valid_topics:
            current_app.logger.warning(f"Invalid topic received: {topic}")
            topic = 'intellectual property issues'  # Default to a safe value
        
        current_app.logger.info(f"Fetching links from Perplexity AI for topic: {topic}")
        
        # Create the prompt with the selected topic
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        prompt = f"""Give me five links to articles from the past week about legal issues involving the tech industry. Focus on articles about {topic}. Be sure to search tech blogs and business news sites. For each article, give me the URL and the date of the article in MM-DD-YYYY format. Don't give me any text or commentary other than the URLs and the dates. Return the data as an array of JSON objects in the following format:

{{
"url": string
"date_of_article": string
}}

Only return the JSON object, nothing else."""
        
        # Prepare the request payload
        payload = {
            "model": "sonar-deep-research",
            "temperature": 0.0,
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful research assistant that provides accurate information with sources."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        # Log the request payload for debugging
        current_app.logger.info(f"Sending request to Perplexity API with payload: {json.dumps(payload)}")
        
        # Make the API request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload
        )
        
        # Check if the request was successful
        if response.status_code != 200:
            current_app.logger.error(f"Perplexity API returned status code {response.status_code}: {response.text}")
            return jsonify({
                'success': False, 
                'error': f"API returned status code {response.status_code}"
            }), 500
        
        # Get the raw content from the response
        response_data = response.json()
        raw_content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        current_app.logger.info(f"Raw content from Perplexity API: {raw_content}")
        
        # Try to parse the response as JSON first
        links_data = []
        try:
            # Look for JSON array in the response
            json_match = re.search(r'\[.*\]', raw_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                links_data = json.loads(json_str)
            else:
                # Try to parse the entire response as JSON
                links_data = json.loads(raw_content)
                
            # If links_data is not a list, check if it contains a list
            if not isinstance(links_data, list) and isinstance(links_data, dict):
                for key in links_data:
                    if isinstance(links_data[key], list):
                        links_data = links_data[key]
                        break
                
            current_app.logger.info(f"Successfully parsed JSON data: {links_data}")
        except json.JSONDecodeError:
            current_app.logger.warning(f"Failed to parse JSON from response, falling back to text extraction")
            
            # Extract URLs and dates using regex
            urls = re.findall(r'https?://[^\s\'"]+', raw_content)
            dates = re.findall(r'\b\d{2}-\d{2}-\d{4}\b|\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d{2}-\d{2}\b', raw_content)
            
            current_app.logger.info(f"Extracted URLs: {urls}")
            current_app.logger.info(f"Extracted dates: {dates}")
            
            # Create links data from extracted URLs and dates
            links_data = []
            for i, url in enumerate(urls):
                date = dates[i] if i < len(dates) else None
                links_data.append({
                    "url": url,
                    "date_of_article": date
                })
        
        # Save links to database
        count = 0
        for link_data in links_data:
            url = link_data.get('url')
            date_str = link_data.get('date_of_article')
            
            if not url:
                continue
                
            # Parse the date string
            date_of_article = None
            if date_str:
                try:
                    # Try MM-DD-YYYY format
                    date_of_article = datetime.strptime(date_str, '%m-%d-%Y').date()
                except ValueError:
                    try:
                        # Try YYYY-MM-DD format
                        date_of_article = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            # Try MM/DD/YYYY format
                            date_of_article = datetime.strptime(date_str, '%m/%d/%Y').date()
                        except ValueError:
                            current_app.logger.warning(f"Could not parse date: {date_str}")
            
            # Create new link
            link = NewsLink(
                url=url,
                date_of_article=date_of_article,
                date_fetched=datetime.now().date(),
                article_written=False
            )
            
            db.session.add(link)
            count += 1
        
        # Commit all links at once
        db.session.commit()
        
        return jsonify({
            'success': True,
            'count': count,
            'topic': topic,
            'links': [link.to_dict() for link in NewsLink.query.order_by(NewsLink.date_fetched.desc()).limit(count).all()]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching links from Perplexity: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
