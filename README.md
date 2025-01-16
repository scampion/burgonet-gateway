# Burgonet - AI Enterprise Gateway

<p align="center">
  <img src="frontend/app/static/images/logo.png?raw=true" style="width: 200px; height: auto;" />
</p>

## About

Burgonet Gateway is an enterprise LLM gateway that provides secure access and compliance controls for AI systems.​​​​​​​​​​​​​​​​

The goal is to provide for employees, unit and project access to
cloud based LLL providers or self-hosted models via that single entrypoint.

Users can:
- request new tokens easily in a self-service approach 
- monitor they consumption 

Administrators can :
- configure providers (OpenAI, Claude, DeepSeek, Ollama, ...)
in one place
- set quotas by tokens or balance per user, group or project.
- monitor usage
- audit logs input/outputs
- create access list by rules 



It provides:

- Token-based API authentication
- User management via LDAP
- Nginx configuration management
- Secure token generation and storage

planned: 
- Websso integration
- Quota management (per group / per user)
- Access Control List to dispatch on permise and cloud providers 
- Semantic routing 
- Keywords and PII filtering


The complete documentation is available at [https://burgonet.eu/](https://burgonet.eu/)


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

## Name origin 


The [burgonet](https://en.wikipedia.org/wiki/Burgonet) is an ancient helmet, it's a protection for the brain.
Protect your knowledge 


---

**Note**: This project is under active development. Please report any issues or feature requests through the issue tracker.
