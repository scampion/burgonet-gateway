# Burgonet - AI Enterprise Gateway
[in French](README.fr.md)

<p align="center">
  <img src="docs/images/logo.png?raw=true" style="width: 200px; height: auto;" />
</p>

Burgonet Gateway is an AI enterprise gateway that provides secure access to LLM and compliance controls for AI systems.
It will help organizations to manage their AI governance in a secure and compliant way.

Implement in Rust 🦀


The goal is to provide for employees, unit and project access to
cloud based LLL providers or self-hosted models via that single entrypoint.

<p align="center">
  <img src="docs/images/overview.png?raw=true" " />
</p>

The complete documentation is available at [https://burgonet.eu/](https://burgonet.eu/)

   

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




## Features


## Quickstart 

Download the binary in the [packages](packages) and the configuration file [conf.yml](conf.yml) file,  run it : 

    ./burgonet-gw -c conf.yml 


Open in your browser the URL [http://127.0.0.1:6189/](http://127.0.0.1:6189/)


## License & Fair-code Status

This project is provided under the Commons Clause License Condition v1.0 (see [LICENSE](LICENSE) file for details) and follows the [Fair-code](https://faircode.io) principles:

- Free to use and distribute
- Source code openly available
- Can be extended by anyone
- Commercial use requires permission

The license allows free non-production use. For commercial use or production deployments, please contact the author to discuss licensing options.


## Author & Enterprise Support 

Sébastien Campion - sebastien.campion@foss4.eu


## Name origin 


The [burgonet](https://en.wikipedia.org/wiki/Burgonet) is an ancient helmet, it's a protection for the brain.
Protect your knowledge 


---

**Note**: This project is under active development. Please report any issues or feature requests through the issue tracker.
