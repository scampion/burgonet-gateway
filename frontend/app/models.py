from dataclasses import dataclass

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

        user_key = f"sessions:{self._id}"
        # Check if the session key already exists
        if r.exists(user_key):
            user_data = r.hgetall(user_key)
            self._id = user_data.get(b'id', self._id).decode('utf-8')
            self.dn = user_data.get(b'dn', self.dn).decode('utf-8')
            self.username = user_data.get(b'username', self.username).decode('utf-8') or None
            self.gid = int(user_data.get(b'gid', self.gid).decode('utf-8')) if user_data.get(b'gid') else None
            self.group = user_data.get(b'group', self.group).decode('utf-8') or None
        else:
            # Convert None values to empty strings for Redis storage
            r.hset(user_key, mapping={
                'id': self._id,
                'dn': self.dn,
                'username': self.username,
                'gid': self.gid,
                'group': self.group
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
        user_key = f"sessions:{data['id']}"
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

    def delete_session(self):
        r = redis.Redis(
            host=current_app.config['REDIS_HOST'],
            port=current_app.config['REDIS_PORT'],
            db=current_app.config['REDIS_DB']
        )
        user_key = f"sessions:{self._id}"
        r.delete(user_key)


@dataclass
class Provider:
    provider: str
    api_key: str = 'deepseek:v3'
    proxy_pass: str = 'https://api.deepseek.com/chat/completions'
    location: str = '/api.deepseek.com/v3/chat/completions'
    redis_host: str = 'redis'
    redis_port: str = '6379'
    model_name: str = 'deepseek'
    model_version: str = 'v3'

    def __repr__(self):
        return f'<Provider {self}>'

    def nginx_config(self):
        return {
            'directive': 'location',
            'args': [self.location],
            'block': [
                {'directive': 'set', 'args': ['$apikey', '']},
                {'directive': 'set', 'args': ['$redis_host', self.redis_host]},
                {'directive': 'set', 'args': ['$redis_port', self.redis_port]},
                {'directive': 'set', 'args': ['$access_model_name', self.model_name]},
                {'directive': 'set', 'args': ['$access_model_version', self.model_version]},
                {'directive': 'access_by_lua_file', 'args': ['/etc/nginx/lua-scripts/access.lua']},
                {'directive': 'proxy_pass', 'args': [self.proxy_pass]},
                {'directive': 'proxy_ssl_server_name', 'args': ['on']},
                {'directive': 'proxy_set_header', 'args': ['Host', 'api.deepseek.com']},
                {'directive': 'proxy_set_header', 'args': ['X-Real-IP', '$remote_addr']},
                {'directive': 'proxy_set_header', 'args': ['X-Forwarded-For', '$proxy_add_x_forwarded_for']},
                {'directive': 'proxy_set_header', 'args': ['X-Forwarded-Proto', '$scheme']},
                {'directive': 'proxy_set_header', 'args': ['Content-Type', '$content_type']},
                {'directive': 'proxy_set_header', 'args': ['Authorization', 'Bearer $apikey']},
                {'directive': 'proxy_set_header', 'args': ['Content-Length', '$content_length']},
                {'directive': 'proxy_pass_request_body', 'args': ['on']}
            ]
        }


@dataclass
class DeepSeek(Provider):
    api_key: str = 'deepseek:v3'
    proxy_pass: str = 'https://api.deepseek.com/chat/completions'
    location: str = '/api.deepseek.com/v3/chat/completions'

@dataclass
class OpenAI(Provider):
    api_key: str = 'openai:v1'
    proxy_pass: str = 'https://api.openai.com/v1/engines/davinci/completions'
    location: str = '/api.openai.com/v1/engines/davinci/completions'


@dataclass
class Anthropic(Provider):
    api_key: str = 'anthropic:v1'
    proxy_pass: str = 'https://api.anthropic.com/v1/chat/completions'
    location: str = '/api.anthropic.com/v1/chat/completions'
