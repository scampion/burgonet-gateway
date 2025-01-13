from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, dn, username, gid, group):
        self.id = id
        self.dn = dn
        self.username = username
        self.gid = gid
        self.group = group
        self.is_active = True  # Required by Flask-Login
        self.is_authenticated = True  # Required by Flask-Login
        self.is_anonymous = False  # Required by Flask-Login

    def get_id(self):
        return self.id
