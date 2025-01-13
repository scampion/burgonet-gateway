from flask import Blueprint, redirect, url_for, flash, request
from werkzeug.datastructures import MultiDict
from flask_login import login_user, logout_user, current_user
from .. import ldap_manager, login_manager

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(id):
    # Simple user loader using LDAP
    return {'id': id, 'dn': id}

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    try:
        # First authenticate the user
        auth_result = ldap_manager.authenticate(username, password)
        if not auth_result.status:
            flash('Invalid credentials')
            return redirect(url_for('main.index'))
            
        # Get user details
        user_filter = f'(&(uid={username}){app.config["LDAP_USER_OBJECT_FILTER"]})'
        user_result = ldap_manager.connection.search(
            app.config["LDAP_USER_DN"],
            user_filter,
            attributes=['cn', 'uid', 'gidNumber']
        )
        
        if not user_result.status or not user_result.entries:
            flash('User details not found')
            return redirect(url_for('main.index'))
            
        # Get group details
        gid = user_result.entries[0].gidNumber.values[0]
        group_filter = f'(&(gidNumber={gid}){app.config["LDAP_GROUP_OBJECT_FILTER"]})'
        group_result = ldap_manager.connection.search(
            app.config["LDAP_GROUP_DN"],
            group_filter,
            attributes=['cn', 'gidNumber']
        )
        
        # Create user object
        user = {
            'id': auth_result.user_dn,
            'dn': auth_result.user_dn,
            'username': user_result.entries[0].uid.values[0],
            'gid': gid,
            'group': group_result.entries[0].cn.values[0] if group_result.status and group_result.entries else None
        }
        
        login_user(user)
        return redirect(url_for('main.index'))
        
    except Exception as e:
        flash(f'Login failed: {str(e)}')
        return redirect(url_for('main.index'))

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))
