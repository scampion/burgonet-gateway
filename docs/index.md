<p align="center">
  <img src="images/logo_draw_name_alpha.png" alt="Burgonet Gateway" style="width: 30%">
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
- 📝 Audit Logs: Detailed logging of API requests and responses
- 💾 Audit Storage: Persistent storage of all gateway exchanges with configurable retention periods


Need another feature? Don't hesitate to [send an email](mailto:sebastien.campion@foss4.eu) or [create a GitHub ticket](https://github.com/burgonet-eu/gateway/issues)!



## Quick Links
- [Getting Started](#getting-started)
- [Use Cases](#use-cases)
- [Technical Architecture](#technical-architecture)
- [Configuration](#configuration)
- [API Reference](#api-reference)

--8<-- "docs/getting-started.md"

--8<-- "docs/use-cases.md"