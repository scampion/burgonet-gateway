from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
import json

main_bp = Blueprint('main', __name__)

from ..tokens.routes import get_user_tokens
from ..config import ADMIN_GROUP

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('login.html')

@main_bp.route('/home')
@login_required
def home():
    # Load tokens for the current user from Redis
    user_tokens = get_user_tokens(current_user.get_id())
    return render_template('index.html', tokens=user_tokens, ADMIN_GROUP=ADMIN_GROUP)

