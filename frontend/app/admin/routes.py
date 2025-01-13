from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
import crossplane
import os
from datetime import datetime
from ..config import CROSSPLANE_CONFIG_DIR, CROSSPLANE_BACKUP_DIR

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/nginx-config', methods=['GET', 'POST'])
@login_required
def nginx_config():
    if current_user.gid != 1001:  # Assuming 1001 is the admin group ID
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
