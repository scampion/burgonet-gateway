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
                'expires_at': value
            }
    return tokens

def add_user_token(user_id, token, expires_at):
    """Add a new token for a user with metadata"""
    created_at = datetime.utcnow().isoformat()
    with redis_client.pipeline() as pipe:
        pipe.hset(f'user:{user_id}:tokens', f'token:{token}', expires_at)
        pipe.hset(f'user:{user_id}:tokens', f'meta:{token}:created_at', created_at)
        pipe.execute()

@tokens_bp.route('/tokens', methods=['POST'])
@login_required
def generate_token():
    user_id = current_user.get_id()
    if not user_id:
        return jsonify({'error': 'User not found'}), 404
    
    # Generate secure token
    token = secrets.token_urlsafe(64)
    expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
    
    # Store token in Redis
    add_user_token(user_id, token, expires_at)
    
    return jsonify({
        'token': token,
        'expires_at': expires_at
    }), 201
