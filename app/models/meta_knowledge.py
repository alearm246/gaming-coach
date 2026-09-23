from app import db
from datetime import datetime, timezone
from pgvector.sqlalchemy import Vector


class MetaKnowledge(db.Model):
    __tablename__ = 'meta_knowledge'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(64), nullable=False)  # archetype, card_counter, tip, card_info
    embedding = db.Column(Vector(1536))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<MetaKnowledge {self.title}>'
