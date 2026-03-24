from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.rag import get_coaching_response
from app.models.chat import ChatMessage
from app import db

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/', methods=['POST'])
@jwt_required()
def chat():
    data = request.get_json()
    message = data.get('message')
    player_id = data.get('player_id')
    user_id = int(get_jwt_identity())
    response = get_coaching_response(message, player_id)
    
    if not response:
        return jsonify({'message': 'Failed to get coaching response'}), 500
    
    #we will create two ChatMessages one for the user query and the other for the AI response
    #this is so whenever a user requests a coach response we can augment the last K messages for better context
    try:
        user_chat_msg = ChatMessage(user_id=user_id, role='user', content=message)
        ai_chat_msg = ChatMessage(user_id=user_id, role='assistant', content=response)
        
        db.session.add(user_chat_msg)
        db.session.add(ai_chat_msg)
        db.session.commit()
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'message': f'Server error: {e}'}), 500
    
    return jsonify({'response': response}), 200