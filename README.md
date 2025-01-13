# Burgonet Gateway

![Burgonet Logo](frontend/app/static/images/logo.png?raw=true)

## About

Burgonet Gateway is a secure API gateway management system built with Flask, Redis, and LDAP authentication. It provides:

- Token-based API authentication
- User management via LDAP
- Nginx configuration management
- Secure token generation and storage

## Features

- **Token Management**: Generate, view, and delete API tokens
- **LDAP Authentication**: Integrated with enterprise LDAP systems
- **Redis Storage**: Secure token storage with Redis
- **Nginx Integration**: Manage Nginx configurations through web interface

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

The main configuration file is located at `flask_app/app/config.py`. Key settings include:

- LDAP connection details
- Redis connection settings
- Nginx configuration paths
- Security settings

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Author

Sébastien Campion - sebastien.campion@foss4.eu

---

**Note**: This project is under active development. Please report any issues or feature requests through the issue tracker.
