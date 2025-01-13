from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, dn, username, gid, group):
        self.id = id
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
        return self.id
