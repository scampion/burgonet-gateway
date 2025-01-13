from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
import json

main_bp = Blueprint('main', __name__)

from ..tokens.routes import get_user_tokens

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Load tokens for the current user from Redis
    user_tokens = {
        token: {'expires_at': expires_at}
        for token, expires_at in get_user_tokens(current_user.get_id()).items()
    }
    
    return render_template('index.html', tokens=user_tokens)
