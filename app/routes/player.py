from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.player import Player
from app.models.user import User
from app.services.clash import get_player_info, get_battle_log
from app import db

player_bp = Blueprint('player', __name__)

@player_bp.route('/connect', methods=['POST'])
@jwt_required()
def connect_player_account():
    data = request.get_json()
    player_tag = data.get('player_tag')

    player = get_player_info(player_tag)

    if not player:
        return jsonify({'message': 'player with player tag does not exist'}), 400

    user_id = get_jwt_identity()

    existing_player = Player.query.filter_by(player_tag=player_tag).first()

    if existing_player and existing_player.user_id == user_id:
        return jsonify({'message': 'this player tag is already associated with this account'}), 400
    
    try:
        new_player = Player(user_id=user_id, player_tag=player_tag, player_name=player.get('name'))

        db.session.add(new_player)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Server error'}), 500

    #get battle logs and store embeddings

    return jsonify({'player_tag': player_tag}), 201 


