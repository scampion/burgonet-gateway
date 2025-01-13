from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, dn, username, gid, group):
        self._id = id
        self.dn = dn
        self.username = username
        self.gid = gid
        self.group = group

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
        self._id = data['id']
        self.dn = data['dn']
        self.username = data['username']
        self.gid = data['gid']
        self.group = data['group']
