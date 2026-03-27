from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app import db

auth_bp = Blueprint('auth', __name__)

MIN_PASSWORD_LENGTH = 6

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'message': 'All fields are required'}), 400

    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({'message': f'Password must be at least {MIN_PASSWORD_LENGTH} characters'}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'Username already exists'}), 400

    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({'message': 'Email already exists'}), 400
    
    hashed_password = generate_password_hash(password)

    try:
        new_user = User(username=username, email=email, password_hash=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        token = create_access_token(identity=str(new_user.id))
        return jsonify({'token': token, 'username': username}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    existing_user = User.query.filter_by(email=email).first()

    if not existing_user:
        return jsonify({'message': 'Invalid credentials'}), 401

    if not check_password_hash(existing_user.password_hash, password):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = create_access_token(identity=str(existing_user.id))
    return jsonify({'token': token, 'email': email}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = int(get_jwt_identity())
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'players': [{'id': p.id, 'player_tag': p.player_tag, 'player_name': p.player_name} for p in user.players]
    }), 200
    
    

    
