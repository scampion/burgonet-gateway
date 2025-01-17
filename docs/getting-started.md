# Getting Started with Burgonet Gateway

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/burgonet-gateway.git
   cd burgonet-gateway
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the application by editing `frontend/app/config.py`

4. Run the application:
   ```bash
   python wsgi.py
   ```

## Configuration

The main configuration file is located at `frontend/app/config.py`. Key settings include:

- **LDAP**: Authentication and user management
- **Redis**: Token storage and caching
- **Nginx**: Proxy configuration
- **Security**: Secret keys and access controls

Example configuration:
```python
# LDAP Settings
LDAP_HOST = 'ldap://localhost'
LDAP_BASE_DN = 'dc=mycompany,dc=com'

# Redis Settings
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Security
SECRET_KEY = 'your-secret-key-here'
```

## First Steps

1. Configure your LDAP integration
2. Set up model providers
3. Configure user groups and permissions
4. Set up monitoring and alerts
