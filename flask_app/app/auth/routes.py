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
        result = ldap_manager.authenticate(username, password)
        if result.status:
            user = {'id': result.user_dn, 'dn': result.user_dn}
            login_user(user)
            return redirect(url_for('admin.index'))
    except Exception as e:
        flash('Login failed')
    
    return redirect(url_for('main.index'))

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))
