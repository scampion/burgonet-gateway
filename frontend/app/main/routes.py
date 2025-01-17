import os

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
import json
import duckdb

main_bp = Blueprint('main', __name__)

from ..tokens.routes import get_user_tokens
from ..config import ADMIN_GROUP, MODELS_CONFIG, RESPONSES_LOGFILE


def load_models_config():
    config_path = os.path.join("../admin", MODELS_CONFIG)  # TODO fix this
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(__file__), config_path)
    config_path = os.path.join(config_path)
    with open(config_path) as f:
        return json.load(f)['models']


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('login.html')

@main_bp.route('/home')
@login_required
def home():
    user = current_user.get_id()
    # Connect to DuckDB and read the response.log file
    con = duckdb.connect(database=':memory:')
    con.execute(f"CREATE TABLE response_log AS SELECT * FROM read_json_auto('{RESPONSES_LOGFILE}')")

    # Get stats from DuckDB
    stats = {
        'total_requests': con.execute(f"SELECT COUNT(*) FROM response_log WHERE user = '{user}'").fetchone()[0],
        'successful_requests': con.execute(f"SELECT COUNT(*) FROM response_log WHERE status = '200' AND user = '{user}'").fetchone()[0],
        'failed_requests': con.execute(f"SELECT COUNT(*) FROM response_log WHERE status != '200' AND user = '{user}' ").fetchone()[0],
        'active_users': con.execute("SELECT COUNT(DISTINCT user) FROM response_log WHERE user IS NOT NULL AND user = '{user}'").fetchone()[0],
        'models': []
    }

    # Get model usage stats
    models = load_models_config()
    for model in models:
        model_stats = {
            'name': model['model_name'],
            'requests': con.execute(f"SELECT COUNT(*) FROM response_log WHERE model_name = '{model['model_name']}' AND user = '{user}'").fetchone()[0],
            'success': con.execute(f"SELECT COUNT(*) FROM response_log WHERE model_name = '{model['model_name']}' AND status = '200' AND user = '{user}'").fetchone()[0],
            'errors': con.execute(f"SELECT COUNT(*) FROM response_log WHERE model_name = '{model['model_name']}' AND status != '200' AND user = '{user}'").fetchone()[0]
        }
        stats['models'].append(model_stats)

    # Load tokens for the current user from Redis
    user_tokens = get_user_tokens(user)
    return render_template('index.html', tokens=user_tokens, ADMIN_GROUP=ADMIN_GROUP, stats=stats)

