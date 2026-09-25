# services/clash_client.py
import requests
from urllib.parse import quote
from config import Config

BASE_URL = "https://api.clashroyale.com/v1"
TIMEOUT = 10

class ClashAPIError(Exception):
    pass

class PlayerNotFoundError(ClashAPIError):
    pass

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {Config.CLASH_API_KEY}"})

def normalize_tag(player_tag: str) -> str:
    tag = player_tag.strip().upper()
    return tag if tag.startswith("#") else f"#{tag}"

def _get(path: str):
    try:
        response = session.get(f"{BASE_URL}{path}", timeout=TIMEOUT)
    except requests.exceptions.RequestException as e:
        raise ClashAPIError(f"Could not reach Clash Royale API: {e}")

    if response.status_code == 404:
        raise PlayerNotFoundError("Player not found")
    if not response.ok:
        raise ClashAPIError(f"Clash Royale API error {response.status_code}: {response.text}")

    return response.json()

def _encoded(player_tag: str) -> str:
    return quote(normalize_tag(player_tag), safe="")

def get_player_info(player_tag: str) -> dict:
    return _get(f"/players/{_encoded(player_tag)}")

def get_battle_log(player_tag: str) -> list:
    return _get(f"/players/{_encoded(player_tag)}/battlelog")

def get_all_cards() -> list:
    return _get("/cards").get("items", [])