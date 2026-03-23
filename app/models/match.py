from app import db
from datetime import datetime, timezone
from pgvector.sqlalchemy import Vector

class Match(db.Model):
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    raw_data = db.Column(db.JSON, nullable=False)
    natural_language_text = db.Column(db.Text, nullable=False)
    embedding = db.Column(Vector(1536))
    result = db.Column(db.String(10), nullable=False)
    match_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Match {self.id} {self.result}>'