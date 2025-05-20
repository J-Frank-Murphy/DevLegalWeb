from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean
from src.models import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_admin = Column(Boolean, default=False)
    
    def __repr__(self):
        return f'<User {self.username}>'
