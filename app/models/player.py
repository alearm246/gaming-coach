from app import db
from datetime import datetime, timezone

class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),  nullable=False)
    player_tag = db.Column(db.String(120), unique=True, nullable=False)
    player_name = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_synced_at = db.Column(db.DateTime)

    matches = db.relationship('Match', backref='player', lazy=True)


    def __repr__(self):
        return f'<Player {self.player_tag}>'