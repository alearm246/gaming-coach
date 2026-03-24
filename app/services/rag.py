from app.services.clash import serialize_match, get_battle_log
from app.services.embeddings import embed_text
from app.models.player import Player
from app.models.match import Match
from datetime import datetime
from app import db
import traceback


def store_match_embeddings(matches, player_id):
    try:
        for match in matches:
            # skip matches that don't have standard 1v1 structure
            if not match.get('team') or not match.get('opponent'):
                continue
            if len(match['team']) == 0 or len(match['opponent']) == 0:
                continue
            
            match_text = serialize_match(match)
            embedding = embed_text(match_text)

            player_battle_data = match['team'][0]
            opponent_battle_data = match['opponent'][0]

            player_crowns = player_battle_data['crowns']
            opponent_crowns = opponent_battle_data['crowns']
            result = 'won' if player_crowns > opponent_crowns else 'lost'
            match_date = datetime.strptime(match.get('battleTime'), '%Y%m%dT%H%M%S.%fZ')

            match_row = Match(player_id=player_id, raw_data=match, 
                    natural_language_text=match_text, embedding=embedding,
                    result=result, match_date=match_date)
            db.session.add(match_row)
            
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f'Error: {e}')
        traceback.print_exc()
        return None

    
