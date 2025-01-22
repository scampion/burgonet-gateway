<p align="center">
  <img src="images/logo_small.png" alt="Burgonet Gateway">
</p>


**AI enterprise gateway** implemented in Rust 🦀 that provides secure, governed access to LLMs (Large Language Models) for 
organizations. It acts as a single entry point for employees and projects to access both cloud-based and self-hosted AI models 
while enforcing security, compliance, and usage controls. The software helps organizations manage AI governance by 
providing centralized control over model access, usage tracking, and security policies.


## Features

- 🔑 **Token Management**: Generate, view, and delete API tokens
- 🎯 **Quota Management**: Set token quotas per user, group or project
- 📊 **Usage Monitoring**: Real-time usage tracking and analytics
- 🤖 **Provider Management**: Configure multiple LLM providers (OpenAI, Claude, DeepSeek, Ollama, etc.)
- ⏱️ **Rate Limiting**: Built-in rate limiting with configurable thresholds
- 📝 **Audit Logs**: Detailed logging of API requests and responses
- 🖥️ **Embedded Web UI**: Built-in admin interface for configuration and monitoring
- 🔒 **PII Protection**: Built-in Personally Identifiable Information detection and blocking
- 📈 **Prometheus Metrics**: Built-in Prometheus endpoint for monitoring and alerting
- 🔐 **Trusted Header Authentication**: Support for authentication via trusted HTTP headers
- 🚫 **Content Filtering**: Block requests containing blacklisted words (e.g. "confidential")
- 🚷 **Group Access Control**: Restrict access by user groups with disabled_groups configuration

Need another feature? Don't hesitate to [send an email](mailto:sebastien.campion@foss4.eu) or [create a GitHub ticket](https://github.com/burgonet-eu/gateway/issues)!



## Quick Links
- [Getting Started](#getting-started)
- [Core Features](#core-features)
- [Use Cases](#use-cases)
- [Technical Architecture](#technical-architecture)
- [Configuration](#configuration)
- [API Reference](#api-reference)

## Quickstart

Download the binary in the [packages](https://github.com/burgonet-eu/gateway/releases/) and the configuration file [conf.yml](https://github.com/burgonet-eu/gateway/blob/main/conf.yml) file,  run it :

    ./burgonet-gw -c conf.yml 


Open in your browser the URL [http://127.0.0.1:6189/](http://127.0.0.1:6189/)


--8<-- "docs/use-cases.md"