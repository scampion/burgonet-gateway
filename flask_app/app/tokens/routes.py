from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..config import TOKENS_FILE
import secrets
from datetime import datetime, timedelta
import json
import os

tokens_bp = Blueprint('tokens', __name__)

def load_tokens():
    if not os.path.exists(TOKENS_FILE):
        return {}
    with open(TOKENS_FILE) as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKENS_FILE, 'w') as f:
        json.dump(tokens, f)

@tokens_bp.route('/tokens', methods=['POST'])
@login_required
def generate_token():
    user_dn = current_user.get('dn')
    if not user_dn:
        return jsonify({'error': 'User not found'}), 404
    
    # Generate secure token
    token = secrets.token_urlsafe(64)
    expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
    
    # Store token
    tokens = load_tokens()
    tokens[token] = {
        'user_dn': user_dn,
        'created_at': datetime.utcnow().isoformat(),
        'expires_at': expires_at
    }
    save_tokens(tokens)
    
    return jsonify({
        'token': token,
        'expires_at': expires_at
    }), 201
