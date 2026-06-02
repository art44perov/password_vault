from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class VaultConfig(db.Model):
    __tablename__ = 'vault_config'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VaultEntry(db.Model):
    __tablename__ = 'vault_entries'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    username = db.Column(db.Text)
    password = db.Column(db.Text)
    url = db.Column(db.Text)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='other')
    tags = db.Column(db.Text, default='')
    color = db.Column(db.String(20), default='default')
    is_favorite = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_encrypted=False):
        return {
            'id': self.id,
            'title': self.title,
            'username': self.username,
            'url': self.url,
            'description': self.description,
            'category': self.category,
            'tags': self.tags.split(',') if self.tags else [],
            'color': self.color,
            'is_favorite': self.is_favorite,
            'is_archived': self.is_archived,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'password': self.password if include_encrypted else None,
        }
