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