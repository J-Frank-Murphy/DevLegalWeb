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
        
        # Save the focus_of_article field immediately, even if article generation fails
        # This ensures the focus is saved as if the user had clicked the Save button
        link.focus_of_article = data['focus_of_article']
        db.session.commit()
        
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
                'post_title': post.title,
                'post_slug': post.slug,
                'post_excerpt': post.excerpt
            })
            
        except (json.JSONDecodeError, KeyError) as e:
            current_app.logger.error(f"Error parsing OpenAI response: {e}")
            return jsonify({'error': f'Error parsing OpenAI response: {e}'}), 500
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error generating article: {e}")
        return jsonify({'error': str(e)}), 500

def extract_urls_and_dates(text):
    """
    Extract URLs and associated dates from unstructured text.
    
    This function uses regex to find URLs and dates in any format, then
    associates each URL with the closest date that appears near it.
    
    Args:
        text (str): The unstructured text to parse
    
    Returns:
        list: A list of dictionaries with 'url' and 'date_of_article' keys
    """
    # Regex for finding URLs
    # This pattern matches common URL formats including http, https, www prefixes
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!.~\'*,;:=+$/?#[\]@&]+)*'
    
    # Regex patterns for finding dates in various formats
    date_patterns = [
        # MM-DD-YYYY or MM/DD/YYYY
        r'(0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])[-/](20\d{2})',
        # YYYY-MM-DD or YYYY/MM/DD
        r'(20\d{2})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])',
        # Month DD, YYYY (e.g., January 1, 2023)
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(0?[1-9]|[12]\d|3[01]),?\s+(20\d{2})',
        # Abbreviated month (e.g., Jan 1, 2023)
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(0?[1-9]|[12]\d|3[01]),?\s+(20\d{2})',
        # DD Month YYYY (e.g., 1 January 2023)
        r'(0?[1-9]|[12]\d|3[01])\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d{2})',
        # DD abbreviated month YYYY (e.g., 1 Jan 2023)
        r'(0?[1-9]|[12]\d|3[01])\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(20\d{2})'
    ]
    
    # Find all URLs in the text
    urls = re.findall(url_pattern, text)
    
    # Clean and validate URLs
    valid_urls = []
    for url in urls:
        # Normalize URL
        url = url.strip()
        
        # Skip empty URLs
        if not url:
            continue
            
        # Ensure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Validate URL format
        try:
            parsed = urllib.parse.urlparse(url)
            if all([parsed.scheme, parsed.netloc]):
                valid_urls.append(url)
        except Exception as e:
            current_app.logger.warning(f"Invalid URL format: {url}, error: {e}")
            continue
    
    # Find all dates in the text
    all_dates = []
    for pattern in date_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            date_str = match.group(0)
            position = match.start()
            all_dates.append((date_str, position))
    
    # Sort dates by their position in the text
    all_dates.sort(key=lambda x: x[1])
    
    # Find positions of all URLs in the text
    url_positions = []
    for url in valid_urls:
        # Find all occurrences of this URL in the text
        for match in re.finditer(re.escape(url), text):
            url_positions.append((url, match.start()))
    
    # Sort URLs by their position in the text
    url_positions.sort(key=lambda x: x[1])
    
    # Associate each URL with the nearest date
    results = []
    
    # If we have URLs but no dates, add URLs with None dates
    if url_positions and not all_dates:
        for url, _ in url_positions:
            results.append({
                'url': url,
                'date_of_article': None
            })
        return results
    
    # If we have dates but no URLs, return empty list
    if not url_positions:
        return []
    
    # Process URLs and associate with dates
    for i, (url, url_pos) in enumerate(url_positions):
        # Find the closest date before or after this URL
        closest_date = None
        min_distance = float('inf')
        
        for date_str, date_pos in all_dates:
            distance = abs(url_pos - date_pos)
            
            # If this is the closest date so far, use it
            if distance < min_distance:
                min_distance = distance
                closest_date = date_str
        
        # Parse the date if we found one
        parsed_date = None
        if closest_date:
            parsed_date = parse_date_string(closest_date)
        
        # Add the URL and date to results
        results.append({
            'url': url,
            'date_of_article': parsed_date
        })
    
    return results

def parse_date_string(date_str):
    """
    Parse a date string in various formats and return a datetime.date object.
    
    Args:
        date_str (str): The date string to parse
    
    Returns:
        datetime.date or None: The parsed date or None if parsing fails
    """
    # List of date formats to try
    formats = [
        '%m-%d-%Y',  # MM-DD-YYYY
        '%m/%d/%Y',  # MM/DD/YYYY
        '%Y-%m-%d',  # YYYY-MM-DD
        '%Y/%m/%d',  # YYYY/MM/DD
        '%B %d, %Y',  # Month DD, YYYY
        '%B %d %Y',   # Month DD YYYY
        '%b %d, %Y',  # Abbreviated month DD, YYYY
        '%b %d %Y',   # Abbreviated month DD YYYY
        '%d %B %Y',   # DD Month YYYY
        '%d %b %Y',   # DD Abbreviated month YYYY
    ]
    
    # Try each format
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # If all formats fail, log warning and return None
    current_app.logger.warning(f"Could not parse date: {date_str}")
    return None

@news_links_bp.route('/api/fetch-perplexity', methods=['POST'])
@login_required
def fetch_perplexity_links():
    """
    Show the JSON object that would be sent to Perplexity AI for debugging.
    
    This version returns the payload that would be sent to Perplexity AI
    without actually making the API call or saving anything to the database.
    """
    # Check if Perplexity API key is configured
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if not api_key:
        current_app.logger.error("Perplexity API key not found in environment variables")
        return jsonify({'error': 'Perplexity API key not configured. Please set the PERPLEXITY_API_KEY environment variable.'}), 500
    
    try:
        # Get yesterday's date for the prompt
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%B %d, %Y')
        
        # Construct the prompt for Perplexity AI
        prompt = f"""Give me ten links to articles from {yesterday} (or thereabouts) about news stories, announcements by tech companies, court cases, regulatory actions, or other occurrences that relate to the intersection of law, technology, and business. Focus on articles about intellectual property issues, open source licensing and compliance, and data privacy. For each article, give me the URL and the date of the article in MM-DD-YYYY format."""
        
        # Prepare the request payload that would be sent to Perplexity API
        payload = {
            "model": "sonar-deep-research",
            "temperature": 0.0,
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that researches news stories about law, technology, and business."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]    
        }
        
        # Log the payload (without API key)
        current_app.logger.info(f"Payload that would be sent to Perplexity API: {payload}")
        
        # Return the payload for debugging
        return jsonify({
            'debug': True,
            'request_payload': payload,
            'message': 'This is the JSON object that would be sent to Perplexity AI for debugging purposes. No API call has been made and no links have been saved to the database.'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error preparing Perplexity request: {str(e)}")
        return jsonify({'error': f'Error preparing Perplexity request: {str(e)}'}), 500
