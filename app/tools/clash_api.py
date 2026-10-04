from langchain_core.tools import tool
from services.clash import get_player_info, ClashAPIError, PlayerNotFoundError

def make_clash_tools(player_tag: str):
    @tool
    def get_player_profile() -> str:
        """Get the user's live Clash Royale profile: trophies, best trophies,
        arena, total wins and losses, and their current battle deck with card
        levels and elixir costs. Use this for questions about their current
        deck, trophy count, or overall stats."""
        try:
            p = get_player_info(player_tag)
        except PlayerNotFoundError:
            return "The player's tag could not be found in Clash Royale."
        except ClashAPIError:
            return "The Clash Royale API is unavailable right now."

        deck = ", ".join(
            f"{c['name']} (level {c['level']}, {c.get('elixirCost', '?')} elixir)"
            for c in p.get("currentDeck", [])
        )
        return (
            f"Name: {p['name']}\n"
            f"Trophies: {p.get('trophies')} (best: {p.get('bestTrophies')})\n"
            f"Arena: {p.get('arena', {}).get('name')}\n"
            f"Wins: {p.get('wins')}, Losses: {p.get('losses')}\n"
            f"Current deck: {deck}"
        )

    return [get_player_profile]