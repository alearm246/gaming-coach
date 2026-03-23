import requests
import os

BASE_URL = "https://api.clashroyale.com/v1"

def get_battle_log(player_tag):
    #URLs already resesrve # for something else we need to replace with %23
    try:
        url = f"{BASE_URL}/players/{player_tag.replace('#', '%23')}/battlelog"
        response = requests.get(url, headers={
            'Authorization': f"Bearer {os.getenv('CLASH_API_KEY')}"
        })
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

def get_player_info(player_tag):
    try:
        url = f"{BASE_URL}/players/{player_tag.replace('#', '%23')}"
        response = requests.get(url, headers={
            'Authorization': f"Bearer {os.getenv('CLASH_API_KEY')}"
        })
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

#Takes the raw JSON that represents a 'match' and converts it into natural language representation
def serialize_match(match):
    player_battle_data = match['team'][0]
    opponent_battle_data = match['opponent'][0]

    player_crowns = player_battle_data['crowns']
    opponent_crowns = opponent_battle_data['crowns']
    result = 'won' if player_crowns > opponent_crowns else 'lost'

    team_deck = get_deck_info(player_battle_data['cards'])
    opponent_deck = get_deck_info(opponent_battle_data['cards'])

    player_elixir_leaked = player_battle_data.get('elixirLeaked', 0)
    opponent_elixir_leaked = opponent_battle_data.get('elixirLeaked', 0)

    king_tower_hp = player_battle_data.get('kingTowerHitPoints', 0)
    princess_towers = player_battle_data.get('princessTowersHitPoints')

    if princess_towers:
        tower_status = f"Princess towers had {princess_towers[0]} and {princess_towers[1]} HP remaining."
    else:
        tower_status = "All towers were destroyed."

    return (
        f"Player {result} the match {player_crowns}-{opponent_crowns} crowns. "
        f"Player used: {team_deck}. "
        f"Opponent used: {opponent_deck}. "
        f"Player leaked {player_elixir_leaked} elixir, opponent leaked {opponent_elixir_leaked} elixir. "
        f"Player king tower had {king_tower_hp} HP remaining. "
        f"{tower_status}"
    )



def get_deck_info(cards):
    deck = []
    for card in cards:
        name = card['name']
        level = card['level']
        max_level = card['maxLevel']
        elixir = card['elixirCost']
        deck.append(f"{name} (level {level}/{max_level}, {elixir} elixir)")
    return ', '.join(deck)

    
