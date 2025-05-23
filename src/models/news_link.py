from datetime import datetime
from src import db

class NewsLink(db.Model):
    """
    Model for news links to be tracked for article writing.
    """
    __tablename__ = 'news_links'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text, nullable=False)
    date_of_article = db.Column(db.Date, nullable=True)
    date_fetched = db.Column(db.Date, nullable=True)
    article_written = db.Column(db.Boolean, default=False)
    focus_of_article = db.Column(db.Text, nullable=True)
    
    def __init__(self, url, date_of_article=None, date_fetched=None, article_written=False, focus_of_article=None):
        self.url = url
        self.date_of_article = date_of_article
        self.date_fetched = date_fetched if date_fetched else datetime.now().date()
        self.article_written = article_written
        self.focus_of_article = focus_of_article
    
    def to_dict(self):
        """
        Convert the model instance to a dictionary for JSON serialization.
        """
        return {
            'id': self.id,
            'url': self.url,
            'date_of_article': self.date_of_article.isoformat() if self.date_of_article else None,
            'date_fetched': self.date_fetched.isoformat() if self.date_fetched else None,
            'article_written': self.article_written,
            'focus_of_article': self.focus_of_article
        }
