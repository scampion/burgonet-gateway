from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from ..config import TOKENS_FILE
import json

main_bp = Blueprint('main', __name__)

def load_tokens():
    try:
        with open(TOKENS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Load tokens for the current user
    tokens = load_tokens()
    user_tokens = {
        token: details for token, details in tokens.items() 
        if details.get('user_dn') == current_user.dn
    }
    
    return render_template('index.html', tokens=user_tokens)
