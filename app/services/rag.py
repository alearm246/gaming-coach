from app.services.clash import serialize_match, get_battle_log
from app.services.embeddings import embed_text
from app.models.player import Player
from app.models.match import Match
from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import text
from openai import OpenAI
import os
from app import db
import traceback

VALID_GAME_MODES = {'PvP', 'pathOfLegend'}

SYSTEM_PROMPT = """You are an expert Clash Royale coach with deep knowledge of the game's mechanics, cards, and meta.
You have access to the player's recent match history provided as context below.

When answering questions:
- Prioritize insights from the player's actual match data when relevant
- Be specific and actionable — don't give generic advice
- Reference specific matches or patterns you notice in their data
- For questions not related to their match history, draw on your general Clash Royale knowledge
- Keep responses concise and focused
- Speak directly to the player, not about them"""

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def store_match_embeddings(matches, player_id):
    try:
        for match in matches:
            # skip matches that don't have standard 1v1 structure
            if not match.get('team') or not match.get('opponent'):
                continue
            if len(match['team']) == 0 or len(match['opponent']) == 0:
                continue
            if match.get('type') not in VALID_GAME_MODES:
                continue
            
            print(f"Match type: {match.get('type')}")
            
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
    
def get_coaching_response(user_query, player_id):
    user_query_embedding = embed_text(user_query)
    matches = Match.query.filter_by(player_id=player_id)\
    .order_by(Match.embedding.op('<->')(user_query_embedding))\
    .limit(5)\
    .all()
    
    augmented_response = []
    for match in matches:
        augmented_response.append(match.natural_language_text)
    
    context = '\n'.join(augmented_response)
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\nPlayer's Recent Match History:\n" + context},
        {"role": "user", "content": user_query}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None
    
    return response.choices[0].message.content
    
