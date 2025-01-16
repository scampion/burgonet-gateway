import os

# Syslog server
SYSLOG_HOST = 'm1'
SYSLOG_PORT = 5140

RESPONSES_LOGFILE = 'responses.log'

EXPIRATION_TIME = 60 * 60 * 24 * 7  # 1 week

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Security
SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
LDAP_HOST = 'ldap://localhost'
LDAP_BASE_DN = 'dc=mycompany,dc=com'
LDAP_USER_DN = 'ou=people,dc=mycompany,dc=com'
LDAP_GROUP_DN = 'ou=groups,dc=mycompany,dc=com'
LDAP_USER_OBJECT_FILTER = '(|(objectClass=inetOrgPerson)(objectClass=posixAccount))'
LDAP_GROUP_OBJECT_FILTER = '(objectClass=posixGroup)'
LDAP_BIND_USER_DN = 'cn=admin,dc=mycompany,dc=com'
LDAP_BIND_USER_PASSWORD = 'adminpassword'


# Data storage
DATA_DIR = os.path.join(BASE_DIR, 'data')
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
REDIS_API_KEY_PREFIX = 'api:'

# Crossplane
CROSSPLANE_CONFIG = './nginx-conf/nginx.conf'
CROSSPLANE_BACKUP_DIR = './nginx-conf/backups'
CROSSPLANE_CONFIG_DIR = './nginx-conf/conf.d'
MODELS_CONFIG = './config/models.json'

# Admin group ID
ADMIN_GROUP = 1000
