import json
from collections import defaultdict

from app import db
from app.models.match import Match
from app.models.player import Player
from app.models.meta_knowledge import MetaKnowledge
from app.services.clash import get_player_info, get_player_cards
from app.services.embeddings import embed_text


def get_player_profile(player_id: int) -> dict:
    player = Player.query.get(player_id)
    if not player:
        return {'error': 'Player not found'}

    api_data = get_player_info(player.player_tag) or {}

    return {
        'player_tag': player.player_tag,
        'player_name': player.player_name,
        'last_synced_at': player.last_synced_at.isoformat() if player.last_synced_at else None,
        'trophies': api_data.get('trophies'),
        'best_trophies': api_data.get('bestTrophies'),
        'arena': api_data.get('arena', {}).get('name'),
        'wins': api_data.get('wins'),
        'losses': api_data.get('losses'),
        'battle_count': api_data.get('battleCount'),
        'three_crown_wins': api_data.get('threeCrownWins'),
        'current_favourite_card': api_data.get('currentFavouriteCard', {}).get('name'),
        'clan': api_data.get('clan', {}).get('name'),
    }


def get_recent_matches(player_id: int, limit: int = 10) -> list:
    limit = min(limit, 25)
    matches = (
        Match.query
        .filter_by(player_id=player_id)
        .order_by(Match.match_date.desc())
        .limit(limit)
        .all()
    )
    return [m.natural_language_text for m in matches]


def search_match_history(player_id: int, query: str, limit: int = 5) -> list:
    query_embedding = embed_text(query)
    if query_embedding is None:
        return []

    matches = (
        Match.query
        .filter(Match.player_id == player_id, Match.embedding.isnot(None))
        .order_by(Match.embedding.op('<->')(query_embedding))
        .limit(limit)
        .all()
    )
    return [m.natural_language_text for m in matches]


def get_player_deck_stats(player_id: int) -> dict:
    matches = Match.query.filter_by(player_id=player_id).all()
    if not matches:
        return {'error': 'No match history found'}

    archetype_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'elixir_leaked': []})
    card_frequency = defaultdict(int)
    total_elixir_leaked = []
    total_avg_elixir = []

    for m in matches:
        arch = m.player_deck_archetype or 'unknown'
        if m.result == 'won':
            archetype_stats[arch]['wins'] += 1
        else:
            archetype_stats[arch]['losses'] += 1
        archetype_stats[arch]['elixir_leaked'].append(m.elixir_leaked or 0)

        if m.player_cards:
            for card in m.player_cards:
                card_frequency[card] += 1

        if m.elixir_leaked is not None:
            total_elixir_leaked.append(m.elixir_leaked)
        if m.avg_elixir_cost is not None:
            total_avg_elixir.append(m.avg_elixir_cost)

    archetype_summary = {}
    for arch, stats in archetype_stats.items():
        total = stats['wins'] + stats['losses']
        avg_leaked = sum(stats['elixir_leaked']) / len(stats['elixir_leaked']) if stats['elixir_leaked'] else 0
        archetype_summary[arch] = {
            'wins': stats['wins'],
            'losses': stats['losses'],
            'win_rate': round(stats['wins'] / total * 100, 1) if total else 0,
            'avg_elixir_leaked': round(avg_leaked, 2),
        }

    top_cards = sorted(card_frequency.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        'total_matches': len(matches),
        'overall_win_rate': round(sum(1 for m in matches if m.result == 'won') / len(matches) * 100, 1),
        'avg_elixir_leaked': round(sum(total_elixir_leaked) / len(total_elixir_leaked), 2) if total_elixir_leaked else None,
        'avg_deck_elixir_cost': round(sum(total_avg_elixir) / len(total_avg_elixir), 2) if total_avg_elixir else None,
        'by_archetype': archetype_summary,
        'most_used_cards': [{'card': c, 'games': n} for c, n in top_cards],
    }


def get_player_card_collection(player_id: int) -> list:
    player = Player.query.get(player_id)
    if not player:
        return []

    cards = get_player_cards(player.player_tag)
    if not cards:
        return []

    return [
        {
            'name': c.get('name'),
            'level': c.get('level'),
            'max_level': c.get('maxLevel'),
            'elixir_cost': c.get('elixirCost'),
            'rarity': c.get('rarity'),
        }
        for c in cards
    ]


def get_meta_knowledge(query: str, category: str = None) -> list:
    query_embedding = embed_text(query)
    if query_embedding is None:
        return []

    q = MetaKnowledge.query.filter(MetaKnowledge.embedding.isnot(None))
    if category:
        q = q.filter_by(category=category)

    results = q.order_by(MetaKnowledge.embedding.op('<->')(query_embedding)).limit(5).all()
    return [{'title': r.title, 'content': r.content, 'category': r.category} for r in results]


TOOL_DISPATCH = {
    'get_player_profile': lambda args: get_player_profile(**args),
    'get_recent_matches': lambda args: get_recent_matches(**args),
    'search_match_history': lambda args: search_match_history(**args),
    'get_player_deck_stats': lambda args: get_player_deck_stats(**args),
    'get_player_card_collection': lambda args: get_player_card_collection(**args),
    'get_meta_knowledge': lambda args: get_meta_knowledge(**args),
}

TOOL_DEFINITIONS = [
    {
        'name': 'get_player_profile',
        'description': (
            "Fetches the player's Clash Royale profile including trophies, arena, win/loss record, "
            "favourite card, and clan. Use this first to understand who you're coaching."
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'player_id': {'type': 'integer', 'description': 'Internal database ID of the player'},
            },
            'required': ['player_id'],
        },
    },
    {
        'name': 'get_recent_matches',
        'description': (
            'Returns the N most recent matches in natural language format — decks used, crowns, '
            'elixir leaked, win/loss. Use to see recent performance trends or specific recent games.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'player_id': {'type': 'integer'},
                'limit': {'type': 'integer', 'description': 'Number of matches to return (default 10, max 25)', 'default': 10},
            },
            'required': ['player_id'],
        },
    },
    {
        'name': 'search_match_history',
        'description': (
            'Semantic search over the player\'s match history. Use when the player asks about specific '
            'situations or patterns — e.g. "matches where I lost to beatdown", "games I used Hog Rider", '
            '"my worst elixir leaks".'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'player_id': {'type': 'integer'},
                'query': {'type': 'string', 'description': 'Natural language description of matches to find'},
                'limit': {'type': 'integer', 'default': 5},
            },
            'required': ['player_id', 'query'],
        },
    },
    {
        'name': 'get_player_deck_stats',
        'description': (
            'Aggregated stats from match history: win rate by deck archetype, most-used cards, '
            'average elixir cost, elixir efficiency. Use to identify the player\'s playstyle and '
            'which deck compositions succeed or fail for them.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'player_id': {'type': 'integer'},
            },
            'required': ['player_id'],
        },
    },
    {
        'name': 'get_player_card_collection',
        'description': (
            'Fetches the player\'s card collection: cards owned, their levels, max levels, and elixir cost. '
            'REQUIRED before making any deck recommendations — only recommend decks the player can actually build.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'player_id': {'type': 'integer'},
            },
            'required': ['player_id'],
        },
    },
    {
        'name': 'get_meta_knowledge',
        'description': (
            'Searches the Clash Royale meta knowledge base for information about deck archetypes, '
            'card counters, strategic tips, and current top decks. Use when the player asks about the meta, '
            'wants deck recommendations, or needs context on why certain cards/decks are strong or weak.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string', 'description': 'What to search for, e.g. "beatdown counters", "Goblin Giant weakness"'},
                'category': {
                    'type': 'string',
                    'enum': ['archetype', 'card_counter', 'tip', 'card_info'],
                    'description': 'Optional filter by category',
                },
            },
            'required': ['query'],
        },
    },
]
