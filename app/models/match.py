# models/match.py
from app import db
from datetime import datetime, timezone

class Match(db.Model):
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    result = db.Column(db.String(10), nullable=False)
    elixir_leaked = db.Column(db.Float)
    opponent_elixir_leaked = db.Column(db.Float)
    player_crowns = db.Column(db.Integer)
    opponent_crowns = db.Column(db.Integer)
    trophy_change = db.Column(db.Integer)
    player_deck_archetype = db.Column(db.String(50))
    opponent_deck_archetype = db.Column(db.String(50))
    avg_elixir_cost = db.Column(db.Float)
    opponent_avg_elixir_cost = db.Column(db.Float)
    player_cards = db.Column(db.JSON)
    opponent_cards = db.Column(db.JSON)
    match_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Match {self.id} {self.result}>'