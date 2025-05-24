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

@news_links_bp.route('/api/fetch-perplexity', methods=['POST'])
@login_required
def fetch_perplexity_links():
    """Fetch news links from Perplexity AI and add them to the database"""
    # Check if Perplexity API key is configured
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if not api_key:
        current_app.logger.error("Perplexity API key not found in environment variables")
        return jsonify({'error': 'Perplexity API key not configured. Please set the PERPLEXITY_API_KEY environment variable.'}), 500
    
    try:
        # Get yesterday's date for the prompt
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%B %d, %Y')
        
        # Construct the prompt for Perplexity AI
        prompt = f"""Give me ten links to articles from {yesterday} (or thereabouts) about news stories, announcements by tech companies, court cases, regulatory actions, or other occurrences that relate to the intersection of law, technology, and business. Focus on articles about intellectual property issues, open source licensing and compliance, and data privacy. For each article, give me the URL and the date of the article in MM-DD-YYYY format. Don't give me any text or commentary other than the URLs and the dates. Return the data as an array of JSON objects in the following format:

{{
"url": string
"date_of_article": string
}}

Only return the JSON object, nothing else."""
        
        # Prepare the request to Perplexity API
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "sonar-medium-online",
            "prompt": prompt,
            "temperature": 0.0,
            "max_tokens": 4000
        }
        
        # Log the request (without API key)
        current_app.logger.info(f"Sending request to Perplexity API with prompt: {prompt}")
        
        # Make the request to Perplexity API
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the response
        perplexity_response = response.json()
        
        # Extract the content from the response
        if 'choices' not in perplexity_response or not perplexity_response['choices']:
            raise ValueError("Invalid response format from Perplexity API")
        
        content = perplexity_response['choices'][0]['message']['content']
        
        # Try to extract JSON from the content
        # First, look for JSON array in the content
        try:
            # Try to find JSON array in the content
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                # If no array brackets found, try to parse the whole content
                links_data = json.loads(content)
            else:
                # Extract the JSON array
                json_str = content[start_idx:end_idx]
                links_data = json.loads(json_str)
                
            # Ensure links_data is a list
            if not isinstance(links_data, list):
                if isinstance(links_data, dict):
                    # If it's a single object, wrap it in a list
                    links_data = [links_data]
                else:
                    raise ValueError("Response is not a valid JSON array or object")
                    
        except json.JSONDecodeError:
            current_app.logger.error(f"Failed to parse JSON from Perplexity response: {content}")
            return jsonify({'error': 'Failed to parse JSON from Perplexity response'}), 500
        
        # Validate and process each link
        processed_links = []
        today = datetime.now().date()
        
        for link_data in links_data:
            # Validate required fields
            if not isinstance(link_data, dict) or 'url' not in link_data:
                current_app.logger.warning(f"Skipping invalid link data: {link_data}")
                continue
                
            url = link_data.get('url', '').strip()
            date_str = link_data.get('date_of_article', '').strip()
            
            # Skip if URL is empty
            if not url:
                current_app.logger.warning("Skipping link with empty URL")
                continue
                
            # Parse date if available
            date_of_article = None
            if date_str:
                try:
                    # Try to parse MM-DD-YYYY format
                    date_of_article = datetime.strptime(date_str, '%m-%d-%Y').date()
                except ValueError:
                    try:
                        # Try alternative formats
                        for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%B %d, %Y', '%b %d, %Y']:
                            try:
                                date_of_article = datetime.strptime(date_str, fmt).date()
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        current_app.logger.warning(f"Could not parse date '{date_str}': {e}")
            
            # Create and save the news link
            link = NewsLink(
                url=url,
                date_of_article=date_of_article,
                date_fetched=today,
                article_written=False
            )
            
            db.session.add(link)
            processed_links.append(link.to_dict())
        
        # Commit all links to the database
        db.session.commit()
        
        # Return success response with processed links
        return jsonify({
            'success': True,
            'links': processed_links,
            'count': len(processed_links)
        })
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Request to Perplexity API failed: {str(e)}")
        return jsonify({'error': f'Failed to connect to Perplexity API: {str(e)}'}), 500
    except Exception as e:
        current_app.logger.error(f"Error fetching links from Perplexity: {str(e)}")
        return jsonify({'error': f'Error fetching links from Perplexity: {str(e)}'}), 500
