from dataclasses import dataclass

from flask_login import UserMixin
import redis
from flask import current_app


class User(UserMixin):
    def __init__(self, id, username, gid, groups):
        self._id = id
        self.username = username
        self.gid = gid
        self.groups = groups


        # Store user data in Redis
        r = redis.Redis(
            host=current_app.config['REDIS_HOST'],
            port=current_app.config['REDIS_PORT'],
            db=current_app.config['REDIS_DB']
        )

        # Store groups info in user:" .. user_id .. ":groups
        if self.groups:
            user_groups_key = f"user:{self._id}:groups"
            r.delete(user_groups_key)
            for group in self.groups:
                r.sadd(user_groups_key, group)

        # Session infos
        user_key = f"sessions:{self._id}"
        # Check if the session key already exists
        if r.exists(user_key):
            user_data = r.hgetall(user_key)
            self._id = user_data.get(b'id', self._id).decode('utf-8')
            self.username = user_data.get(b'username', self.username).decode('utf-8') or None
            self.gid = int(user_data.get(b'gid', self.gid).decode('utf-8')) if user_data.get(b'gid') else None
            self.groups = user_data.get(b'groups', "").split() or None
        else:
            # Convert None values to empty strings for Redis storage
            r.hset(user_key, mapping={
                'id': self._id,
                'username': self.username,
                'gid': self.gid,
                'groups': ' '.join(self.groups)
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
            'username': self.username,
            'gid': self.gid,
            'groups': self.groups
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
            self.username = user_data.get(b'username', data['username']).decode('utf-8') or None
            self.gid = int(user_data.get(b'gid', data['gid']).decode('utf-8')) if user_data.get(b'gid') else None
            self.groups = user_data.get(b'groups', "").split() or None
        else:
            # Fallback to session data
            self._id = data['id']
            self.username = data['username']
            self.gid = data['gid']
            self.groups = data['groups']

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
    pii_protection_url: str = ''

    def __repr__(self):
        return f'<Provider {self}>'

    @staticmethod
    def parse_response(response):
        pass

    def nginx_config(self):
        if not self.provider:
            provider = self.__class__.__name__.lower()
        else:
            provider = self.provider
        return {
            'directive': 'location',
            'args': [self.location],
            'block': [
                {'directive': 'set', 'args': ['$apikey', '']},
                {'directive': 'set', 'args': ['$redis_host', self.redis_host]},
                {'directive': 'set', 'args': ['$redis_port', self.redis_port]},
                {'directive': 'set', 'args': ['$model_name', self.model_name]},
                {'directive': 'set', 'args': ['$model_version', self.model_version]},
                {'directive': 'set', 'args': ['$provider', provider]},
                {'directive': 'access_by_lua_file', 'args': ['/etc/nginx/lua-scripts/access.lua']},
                {'directive': 'pii_protection_url', 'args': [self.pii_protection_url]},
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

    def parse_response(response):
        return {
            "tokens_input": response['response_body']['usage']['prompt_tokens'],
            "tokens_output": response['response_body']['usage']['completion_tokens']
        }


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


@dataclass
class Azure(Provider):
    api_key: str = 'azure:v1'
    proxy_pass: 'https://api.azure.com/v1/chat/completions'
    location: str = '/api.azure.com/v1/chat/completions'

    def nginx_config(self):
        """
        Override the nginx_config method to add the endpoint directive
        Azure endpoint can't be resolved by the DNS at runtime
        :return:
        """
        init_config = super().nginx_config()
        init_config['block'].append({'directive': 'set', 'args': ['$endpoint', self.proxy_pass]})
        init_config['block'] = [block for block in init_config['block'] if block['directive'] != 'proxy_pass']
        init_config['block'].append({'directive': 'proxy_pass', 'args': ['$endpoint']})
        return init_config


@dataclass
class Ollama(Provider):

    def parse_response(response):
        return {
            "tokens_input": response['response_body']['prompt_eval_count'],
            "tokens_output": response['response_body']['eval_count']
        }
