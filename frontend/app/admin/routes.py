from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
import crossplane
import os
import redis
from datetime import datetime
from ..config import CROSSPLANE_CONFIG_DIR, CROSSPLANE_BACKUP_DIR, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_API_KEY_PREFIX, ADMIN_GROUP

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/nginx-config', methods=['GET', 'POST'])
@login_required
def nginx_config():
    if current_user.gid != ADMIN_GROUP:
        flash('Access denied')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        config = request.form.get('config')
        try:
            # Parse and validate config
            crossplane.parse(config)
            
            # Backup current config
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(CROSSPLANE_BACKUP_DIR, f'nginx_{timestamp}.conf')
            with open(backup_path, 'w') as f:
                with open(os.path.join(CROSSPLANE_CONFIG_DIR, 'default.conf')) as current:
                    f.write(current.read())
            
            # Write new config
            with open(os.path.join(CROSSPLANE_CONFIG_DIR, 'default.conf'), 'w') as f:
                f.write(config)
            
            flash('Configuration updated successfully')
        except Exception as e:
            flash(f'Error updating configuration: {str(e)}')
    
    # Get current config
    with open(os.path.join(CROSSPLANE_CONFIG_DIR, 'default.conf')) as f:
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


