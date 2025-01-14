from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
import json
from flask_login import login_required, current_user
import crossplane
import os
import redis
from datetime import datetime
from ..config import PROVIDERS_CONFIG, CROSSPLANE_CONFIG, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_API_KEY_PREFIX, \
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


def load_providers_config():
    config_path = PROVIDERS_CONFIG
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(__file__), config_path)
    config_path = os.path.join(config_path)
    with open(config_path) as f:
        return json.load(f)


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
    # print current directory
    print(os.getcwd())
    if current_user.gid != ADMIN_GROUP:
        flash('Access denied')
        return redirect(url_for('main.index'))

    try:
        # Load base config
        with open(CROSSPLANE_CONFIG) as f:
            base_config = f.read()

        # Parse base config
        parsed = crossplane.parse(base_config)

        # Load providers config
        providers_config = load_providers_config()

        # Get Redis connection
        r = get_redis_connection()

        # Generate location blocks using Provider classes
        location_blocks = []
        for provider_config in providers_config['providers']:
            # Get API key from Redis
            redis_key = f"{REDIS_API_KEY_PREFIX}{provider_config['model']}:v1"
            api_key = r.get(redis_key)
            if api_key:
                provider_config['apikey'] = api_key.decode('utf-8')
                location_blocks.append(generate_location_block(provider_config, api_key.decode('utf-8')))

        # Insert location blocks into server block
        for block in parsed['config']:
            if block['directive'] == 'http':
                for server_block in block['block']:
                    if server_block['directive'] == 'server':
                        # Add location blocks
                        server_block['block'].extend([
                            crossplane.builder.build(loc)
                            for loc in location_blocks
                        ])

        # Generate new config
        new_config = crossplane.builder.build(parsed['config'])

        # Save new config
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(CROSSPLANE_BACKUP_DIR, f'nginx_{timestamp}.conf')
        with open(backup_path, 'w') as f:
            f.write(base_config)

        with open(os.path.join(CROSSPLANE_CONFIG_DIR, 'default.conf'), 'w') as f:
            f.write(new_config)

        flash('Configuration built and updated successfully')
        return jsonify({'status': 'success', 'message': 'Configuration updated'})

    except Exception as e:
        flash(f'Error building configuration: {str(e)}')
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/admin/apikeys', methods=['GET', 'POST'])
@login_required
def redis_keys():
    print(current_user.gid)
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
