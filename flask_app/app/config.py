import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Security
SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
LDAP_HOST = 'ldap://localhost'
LDAP_BASE_DN = 'dc=mycompany,dc=com'
LDAP_USER_DN = 'ou=People,dc=mycompany,dc=com'
LDAP_GROUP_DN = 'ou=Group,dc=mycompany,dc=com'
LDAP_USER_OBJECT_FILTER = '(|(objectClass=inetOrgPerson)(objectClass=posixAccount))'
LDAP_GROUP_OBJECT_FILTER = '(objectClass=posixGroup)'

# Data storage
DATA_DIR = os.path.join(BASE_DIR, 'data')
TOKENS_FILE = os.path.join(DATA_DIR, 'tokens.json')

# Crossplane
CROSSPLANE_CONFIG_DIR = '/etc/nginx/conf.d'
CROSSPLANE_BACKUP_DIR = '/var/backups/nginx'
