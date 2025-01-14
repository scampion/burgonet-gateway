from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
import json
from flask_login import login_required, current_user
import crossplane
import os
import redis
from datetime import datetime
from ..config import MODELS_CONFIG, CROSSPLANE_CONFIG, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_API_KEY_PREFIX, \
    ADMIN_GROUP
from ..models import Provider, DeepSeek, OpenAI, Anthropic

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/nginx-config', methods=['GET', 'POST'])
@login_required
def nginx_config():
    if current_user.gid != ADMIN_GROUP:
        flash('Access denied')
        return redirect(url_for('main.index'))

    crossplane_config_dir = os.path.dirname(CROSSPLANE_CONFIG)
    if request.method == 'POST':
        config = request.form.get('config')
        try:
            # Parse and validate config
            crossplane.parse(config)

            # Write new config
            with open(os.path.join(crossplane_config_dir, 'burgonet.conf'), 'w') as f:
                f.write(config)

            flash('Configuration updated successfully')
        except Exception as e:
            flash(f'Error updating configuration: {str(e)}')

    # Get current config
    with open(os.path.join(crossplane_config_dir, 'burgonet.conf')) as f:
        current_config = f.read()

    return render_template('admin/nginx_config.html', config=current_config)


def get_redis_connection():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


@admin_bp.route('/admin/apikeys/add', methods=['POST'])
@login_required
def add_key():
    if current_user.gid != ADMIN_GROUP:
        flash('Access denied')
        return redirect(url_for('main.index'))

    model = request.form.get('model')
    version = request.form.get('version')
    value = request.form.get('value')

    if not all([model, version, value]):
        flash('All fields are required')
        return redirect(url_for('admin.redis_keys'))

    r = get_redis_connection()
    key = f"{REDIS_API_KEY_PREFIX}{model}:{version}"

    if r.exists(key):
        flash('Key already exists')
    else:
        r.set(key, value)
        flash('Key added successfully')

    return redirect(url_for('admin.redis_keys'))


@admin_bp.route('/admin/apikeys/delete/<key>', methods=['POST'])
@login_required
def delete_key(key):
    if current_user.gid != ADMIN_GROUP:
        flash('Access denied')
        return redirect(url_for('main.index'))

    r = get_redis_connection()
    if r.delete(key):
        flash('Key deleted successfully')
    else:
        flash('Key not found')

    return redirect(url_for('admin.redis_keys'))


def load_models_config():
    config_path = MODELS_CONFIG
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(__file__), config_path)
    config_path = os.path.join(config_path)
    with open(config_path) as f:
        return json.load(f)['models']


def get_provider_class(provider_name):
    """Get the appropriate Provider subclass based on provider name"""
    provider_classes = {
        'deepseek': DeepSeek,
        'openai': OpenAI,
        'anthropic': Anthropic
    }
    return provider_classes.get(provider_name.lower(), Provider)


def generate_location_block(provider_config, api_key):
    """Generate location block using Provider class methods"""
    provider_class = get_provider_class(provider_config['model'])
    provider = provider_class()

    # Update provider instance with config values
    provider.apikey = api_key
    provider.proxy_pass = provider_config['proxy_pass']
    provider.location = provider_config['location']

    return provider.nginx_config_build()


@admin_bp.route('/admin/build', methods=['POST', 'GET'])
@login_required
def build_config():
    if current_user.gid != ADMIN_GROUP:
        flash('Access denied')
        return redirect(url_for('main.index'))

    try:
        # Parse base config
        parsed = crossplane.parse(CROSSPLANE_CONFIG)
        server = None
        filepath = None

        # Select the burgonet file
        for i, config in enumerate(parsed['config']):
            if config['file'].split(os.sep)[-1] == 'burgonet.conf':
                print("Server config found")
                filepath = config['file']
                server = config['parsed'][0]
                break

        if server is None:
            raise Exception('burgonet.conf not found in base config')

        # remove all the location blocks
        server['block'] = [block for block in server['block'] if block['directive'] != 'location']
        print(server)

        # Generate new location blocks
        for model in load_models_config():
            provider = get_provider_class(model['provider'])(**model)
            server['block'].append(provider.nginx_config())

        # Generate new config
        new_config = crossplane.build([server])

        # Save new config
        with open(os.path.join(filepath), 'w') as f:
            f.write(new_config)

        flash('Configuration built and updated successfully')
        return jsonify({'status': 'success',
                        'message': 'Configuration updated',
                        'filepath': filepath,})

    except Exception as e:
        flash(f'Error building configuration: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/apikeys', methods=['GET', 'POST'])
@login_required
def redis_keys():
    if current_user.gid != ADMIN_GROUP:
        flash('Access denied')
        return redirect(url_for('main.index'))

    r = get_redis_connection()
    keys = []

    if request.method == 'POST':
        # Handle key updates
        for key in request.form:
            if key.startswith('value_'):
                redis_key = key[len('value_'):]
                new_value = request.form[key]
                r.set(redis_key, new_value)
        flash('Keys updated successfully')

    # Get all api:* keys
    for key in r.scan_iter(f"{REDIS_API_KEY_PREFIX}*"):
        key_str = key.decode('utf-8')
        value = r.get(key).decode('utf-8')
        parts = key_str.split(':')
        model = parts[1] if len(parts) > 1 else ''
        version = parts[2] if len(parts) > 2 else ''

        keys.append({
            'full_key': key_str,
            'model': model,
            'version': version,
            'value': value
        })

    return render_template('admin/apikeys.html', keys=keys)
