from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, abort, current_app, json
import json
from flask_login import login_required, current_user
import crossplane
import os
import redis
from datetime import datetime
from ..config import MODELS_CONFIG, CROSSPLANE_CONFIG, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_API_KEY_PREFIX, \
    ADMIN_GROUP
from ..models import Provider, DeepSeek, OpenAI, Anthropic, Azure

admin_bp = Blueprint('admin', __name__)


def get_redis_connection():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


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
        'anthropic': Anthropic,
        'azure': Azure
    }
    return provider_classes.get(provider_name.lower(), Provider)


def get_config_filepath():
    parsed = crossplane.parse(CROSSPLANE_CONFIG)
    for i, config in enumerate(parsed['config']):
        if config['file'].split(os.sep)[-1] == 'burgonet.conf':
            if os.path.isabs(config['file']):
                return config['file']
            else:
                return os.path.join(os.getcwd(), config['file'])
    return None


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
        previous_directives = ''

        # Select the burgonet file
        for config in parsed['config']:
            if config['file'].split(os.sep)[-1] == 'burgonet.conf':
                filepath = config['file']
                for o in config['parsed']:
                    if o['directive'] == 'server':
                        server = o
                    else:
                        previous_directives += crossplane.build([o]) + '\n'
                break

        if server is None:
            raise Exception('burgonet.conf not found in base config')

        # remove all the location blocks
        server['block'] = [block for block in server.get('block', []) if block['directive'] != 'location']

        # Generate new location blocks
        for model in load_models_config():
            provider = get_provider_class(model['provider'])(**model)
            server['block'].append(provider.nginx_config())

        # Generate new config
        new_config_server = crossplane.build([server])

        # Save new config
        with open(os.path.join(filepath), 'w') as f:
            f.write(previous_directives)
            f.write(new_config_server)

        return previous_directives + new_config_server, 200, {'Content-Type': 'text/plain; charset=utf-8'}

    except Exception as e:
        flash(f'Error building configuration: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/admin/dashboard')
@login_required
def dashboard():
    if current_user.gid != ADMIN_GROUP:
        flash('Access denied')
        return redirect(url_for('main.index'))

    # Get stats from Redis
    r = get_redis_connection()
    stats = {
        'total_requests': r.get('stats:total_requests') or 0,
        'successful_requests': r.get('stats:successful_requests') or 0,
        'failed_requests': r.get('stats:failed_requests') or 0,
        'active_users': r.scard('active_users') or 0,
        'models': []
    }

    # Get model usage stats
    models = load_models_config()
    for model in models:
        model_stats = {
            'name': model['model_name'],
            'requests': r.get(f"stats:model:{model['model_name']}:requests") or 0,
            'success': r.get(f"stats:model:{model['model_name']}:success") or 0,
            'errors': r.get(f"stats:model:{model['model_name']}:errors") or 0
        }
        stats['models'].append(model_stats)

    return render_template('admin/dashboard.html',
                           stats=stats,
                           ADMIN_GROUP=ADMIN_GROUP)


@admin_bp.route('/admin/model/<int:model_index>', methods=['GET', 'POST'])
@login_required
def model_config(model_index):
    if current_user.gid != ADMIN_GROUP:
        flash('Access denied')
        return redirect(url_for('main.index'))

    try:
        models = load_models_config()
        
        if model_index >= len(models):
            flash('Invalid model index')
            return redirect(url_for('admin.manage_models'))

        model = models[model_index]
        
        if request.method == 'POST':
            # Update model configuration
            model['disabled_groups'] = request.form.get('disabled_groups', '')
            model['blacklist_words'] = request.form.get('blacklist_words', '')
            
            # Save updated config
            model_config = MODELS_CONFIG
            if not os.path.isabs(model_config):
                model_config = os.path.join(os.path.dirname(__file__), model_config)
            with open(model_config, 'w') as f:
                json.dump({"models": models}, f, indent=4)
            
            # Update redis
            r = get_redis_connection()
            route_path = model['location']
            r.hset(f'routes:{route_path}', 'disabled_groups', model['disabled_groups'])
            r.hset(f'routes:{route_path}', 'blacklist_words', model['blacklist_words'])
            
            flash('Model configuration updated successfully')
            return redirect(url_for('admin.model_config', model_index=model_index))

        # Get current values
        disabled_groups = model.get('disabled_groups', '')
        blacklist_words = model.get('blacklist_words', '')
        
        return render_template('admin/model_config.html',
                             model=model,
                             model_index=model_index,
                             disabled_groups=disabled_groups,
                             blacklist_words=blacklist_words)

    except Exception as e:
        flash(f'Error updating model configuration: {str(e)}')
        return redirect(url_for('admin.manage_models'))


@admin_bp.route('/admin/models', methods=['GET', 'POST'])
@login_required
def manage_models():
    if current_user.gid != ADMIN_GROUP:
        flash('Access denied')
        return redirect(url_for('main.index'))

    try:
        models = load_models_config()

        if request.method == 'POST':
            # Handle form submission
            action = request.form.get('action')

            if action == 'add':
                new_model = {
                    "provider": request.form.get('provider'),
                    "model_name": request.form.get('model_name'),
                    "location": request.form.get('location'),
                    "proxy_pass": request.form.get('proxy_pass'),
                    "api_key": request.form.get('api_key')
                }
                models.append(new_model)
                flash('Model added successfully')

            elif action == 'edit':
                model_index = int(request.form.get('model_index'))
                models[model_index] = {
                    "provider": request.form.get('provider'),
                    "model_name": request.form.get('model_name'),
                    "location": request.form.get('location'),
                    "proxy_pass": request.form.get('proxy_pass'),
                    "api_key": request.form.get('api_key')
                }
                flash('Model updated successfully')

            elif action == 'delete':
                model_index = int(request.form.get('model_index'))
                model = models.pop(model_index)
                # remove the model from redis
                r = get_redis_connection()
                route_path = model['location']
                r.delete(f'routes:{route_path}')
                flash('Model deleted successfully')

            # Save updated config
            model_config = MODELS_CONFIG
            if not os.path.isabs(model_config):
                model_config = os.path.join(os.path.dirname(__file__), model_config)
            with open(model_config, 'w') as f:
                json.dump({"models": models}, f, indent=4)

            # Update redis routes:route_path hset disabled_groups
            r = get_redis_connection()
            for model in models:
                route_path = model['location']
                disabled_groups = model.get('disabled_groups', '')
                r.hset(f'routes:{route_path}', 'disabled_groups', disabled_groups)

            return redirect(url_for('admin.manage_models'))

        return render_template('admin/models.html',
                               models=models,
                               filepath=get_config_filepath(),
                               ADMIN_GROUP=ADMIN_GROUP)

    except Exception as e:
        flash(f'Error managing models: {str(e)}')
        import traceback
        traceback.print_exc()
        return redirect(url_for('admin.manage_models'))
