from app.services.clash import serialize_match
from app.services.embeddings import embed_text
from app.models.match import Match
from datetime import datetime
from app import db
import traceback

VALID_GAME_MODES = {'PvP', 'pathOfLegend'}

SIEGE_CARDS = {'X-Bow', 'Mortar'}
HOG_CARDS = {'Hog Rider'}
TANK_CARDS = {'Giant', 'Golem', 'Giant Skeleton', 'Goblin Giant', 'Lava Hound', 'Balloon'}
GRAVEYARD_CARDS = {'Graveyard'}
CYCLE_CARDS = {'Ice Spirit', 'Skeletons', 'Goblin Barrel'}


def classify_deck_archetype(cards, avg_elixir):
    card_set = set(cards)
    if card_set & SIEGE_CARDS:
        return 'siege'
    if card_set & GRAVEYARD_CARDS:
        return 'graveyard control'
    if card_set & HOG_CARDS and avg_elixir < 3.5:
        return 'hog cycle'
    if card_set & TANK_CARDS and avg_elixir >= 4.0:
        return 'beatdown'
    if avg_elixir < 3.5:
        return 'cycle'
    return 'control'


def store_matches(matches, player_id):
    try:
        for match in matches:
            if not match.get('team') or not match.get('opponent'):
                continue
            if len(match['team']) == 0 or len(match['opponent']) == 0:
                continue
            if match.get('type') not in VALID_GAME_MODES:
                continue

            match_date = datetime.strptime(match.get('battleTime'), '%Y%m%dT%H%M%S.%fZ')

            # Skip duplicates
            if Match.query.filter_by(player_id=player_id, match_date=match_date).first():
                continue

            player_battle_data = match['team'][0]
            opponent_battle_data = match['opponent'][0]

            player_crowns = player_battle_data['crowns']
            opponent_crowns = opponent_battle_data['crowns']
            result = 'won' if player_crowns > opponent_crowns else 'lost'
            player_elixir_leaked = player_battle_data.get('elixirLeaked', 0)
            opponent_elixir_leaked = opponent_battle_data.get('elixirLeaked', 0)
            trophy_change = opponent_battle_data.get('trophyChange', 0)

            player_cards = [card['name'] for card in player_battle_data.get('cards', [])]
            opponent_cards = [card['name'] for card in opponent_battle_data.get('cards', [])]

            elixir_costs = [card.get('elixirCost', 0) for card in player_battle_data.get('cards', []) if card.get('elixirCost')]
            avg_elixir_cost = sum(elixir_costs) / len(elixir_costs) if elixir_costs else 0

            opponent_elixir_costs = [card.get('elixirCost', 0) for card in opponent_battle_data.get('cards', []) if card.get('elixirCost')]
            opponent_avg_elixir_cost = sum(opponent_elixir_costs) / len(opponent_elixir_costs) if opponent_elixir_costs else 0

            natural_language_text = serialize_match(
                player_battle_data, opponent_battle_data,
                result, player_crowns, opponent_crowns,
                player_elixir_leaked, opponent_elixir_leaked
            )

            embedding = embed_text(natural_language_text)

            match_row = Match(
                player_id=player_id,
                natural_language_text=natural_language_text,
                result=result,
                match_date=match_date,
                elixir_leaked=player_elixir_leaked,
                player_crowns=player_crowns,
                opponent_crowns=opponent_crowns,
                trophy_change=trophy_change,
                player_cards=player_cards,
                opponent_cards=opponent_cards,
                avg_elixir_cost=avg_elixir_cost,
                opponent_elixir_leaked=opponent_elixir_leaked,
                opponent_avg_elixir_cost=opponent_avg_elixir_cost,
                player_deck_archetype=classify_deck_archetype(player_cards, avg_elixir_cost),
                opponent_deck_archetype=classify_deck_archetype(opponent_cards, opponent_avg_elixir_cost),
                embedding=embedding
            )
            db.session.add(match_row)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f'Error: {e}')
        traceback.print_exc()
        return None


def get_coaching_response(user_query, player_id, user_id):
    from app.services.coach import run_coaching_agent
    return run_coaching_agent(user_query, player_id, user_id)
