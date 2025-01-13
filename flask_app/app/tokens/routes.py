from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..config import REDIS_HOST, REDIS_PORT, REDIS_DB
import secrets
from datetime import datetime, timedelta
import redis

tokens_bp = Blueprint('tokens', __name__)

# Redis connection
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)

def get_user_tokens(user_id):
    """Get all tokens for a user"""
    token_data = redis_client.hgetall(f'user:{user_id}:tokens')
    tokens = {}
    for key, value in token_data.items():
        if key.startswith('token:'):
            token = key.split(':', 1)[1]
            tokens[token] = {
                'created_at': token_data.get(f'meta:{token}:created_at'),
                'label': value
            }
    return tokens

def add_user_token(user_id, token, label):
    """Add a new token for a user with metadata"""
    created_at = datetime.utcnow().isoformat()
    with redis_client.pipeline() as pipe:
        # Store in user's tokens
        pipe.hset(f'user:{user_id}:tokens', f'token:{token}', label)
        pipe.hset(f'user:{user_id}:tokens', f'meta:{token}:created_at', created_at)
        # Store in nginx_tokens with bearer prefix
        pipe.hset('nginx_tokens:bearer', token, user_id)
        pipe.execute()

@tokens_bp.route('/tokens', methods=['POST'])
@login_required
def generate_token():
    user_id = current_user.get_id()
    if not user_id:
        return jsonify({'error': 'User not found'}), 404
    
    # Get label from request
    label = request.json.get('label')
    if not label:
        return jsonify({'error': 'Label is required'}), 400
    
    # Generate secure token
    token = secrets.token_urlsafe(64)
    
    # Store token in Redis
    add_user_token(user_id, token, label)
    
    return jsonify({
        'token': token,
        'label': label,
        'bearer_token': f'Bearer {token}'  # Return the full bearer token format
    }), 201
