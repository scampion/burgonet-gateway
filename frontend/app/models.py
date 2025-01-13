from flask_login import UserMixin
import redis
from flask import current_app

class User(UserMixin):
    def __init__(self, id, dn, username, gid, group):
        self._id = id
        self.dn = dn
        self.username = username
        self.gid = gid
        self.group = group
        
        # Store user data in Redis
        r = redis.Redis(
            host=current_app.config['REDIS_HOST'],
            port=current_app.config['REDIS_PORT'],
            db=current_app.config['REDIS_DB']
        )
        user_key = f"user:{self._id}"
        # Convert None values to empty strings for Redis storage
        r.hset(user_key, mapping={
            'id': self._id,
            'dn': self.dn,
            'username': self.username or '',
            'gid': self.gid or 0,
            'group': self.group or ''
        })
        r.expire(user_key, 3600)  # Expire after 1 hour

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self._id)

    def __getstate__(self):
        """Tell Flask-Login how to serialize the User object"""
        return {
            'id': self._id,
            'dn': self.dn,
            'username': self.username,
            'gid': self.gid,
            'group': self.group
        }

    def __setstate__(self, data):
        """Tell Flask-Login how to deserialize the User object"""
        # Try to load from Redis first
        r = redis.Redis(
            host=current_app.config['REDIS_HOST'],
            port=current_app.config['REDIS_PORT'],
            db=current_app.config['REDIS_DB']
        )
        user_key = f"user:{data['id']}"
        user_data = r.hgetall(user_key)
        
        if user_data:
            self._id = user_data.get(b'id', data['id']).decode('utf-8')
            self.dn = user_data.get(b'dn', data['dn']).decode('utf-8')
            self.username = user_data.get(b'username', data['username']).decode('utf-8') or None
            self.gid = int(user_data.get(b'gid', data['gid']).decode('utf-8')) if user_data.get(b'gid') else None
            self.group = user_data.get(b'group', data['group']).decode('utf-8') or None
        else:
            # Fallback to session data
            self._id = data['id']
            self.dn = data['dn']
            self.username = data['username']
            self.gid = data['gid']
            self.group = data['group']
