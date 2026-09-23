import json
import os
import anthropic

from app.models.chat import ChatMessage
from app.services.tools import TOOL_DEFINITIONS, TOOL_DISPATCH

MAX_TOOL_ITERATIONS = 8
NUM_CHAT_HISTORY = 10

SYSTEM_PROMPT = """You are an expert Clash Royale coach. You have access to tools that let you look up the player's profile, match history, deck stats, card collection, and meta knowledge.

When coaching:
- Use tools to fetch the specific data you need before answering — don't guess
- Before recommending a deck, always call get_player_card_collection to know what they actually own
- Reference specific matches and patterns from their history, not generic advice
- Be concise and actionable — tell them exactly what to do and why
- Speak directly to the player"""

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    return _client


def run_coaching_agent(user_query: str, player_id: int, user_id: int) -> str | None:
    chat_history = (
        ChatMessage.query
        .filter_by(user_id=user_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(NUM_CHAT_HISTORY)
        .all()
    )

    messages = []
    for msg in chat_history:
        messages.append({'role': msg.role, 'content': msg.content})

    # Inject the player_id into the user query so Claude knows which player to query
    augmented_query = f"[player_id: {player_id}]\n\n{user_query}"
    messages.append({'role': 'user', 'content': augmented_query})

    client = _get_client()
    iterations = 0

    while iterations < MAX_TOOL_ITERATIONS:
        iterations += 1

        response = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        if response.stop_reason == 'end_turn':
            for block in response.content:
                if hasattr(block, 'text'):
                    return block.text
            return None

        if response.stop_reason == 'tool_use':
            tool_use_blocks = [b for b in response.content if b.type == 'tool_use']

            # Append assistant turn with tool_use blocks
            messages.append({'role': 'assistant', 'content': response.content})

            # Execute each tool and collect results
            tool_results = []
            for block in tool_use_blocks:
                try:
                    result = TOOL_DISPATCH[block.name](block.input)
                    tool_results.append({
                        'type': 'tool_result',
                        'tool_use_id': block.id,
                        'content': json.dumps(result),
                    })
                except Exception as e:
                    tool_results.append({
                        'type': 'tool_result',
                        'tool_use_id': block.id,
                        'content': json.dumps({'error': str(e)}),
                        'is_error': True,
                    })

            messages.append({'role': 'user', 'content': tool_results})
            continue

        # Unexpected stop reason
        break

    return None
