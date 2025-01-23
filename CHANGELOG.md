# Changelog

### ✨ **New Features & Enhancements**
- 🧠 **OpenAI API Support**: Added support for OpenAI API integration.
  - Now you can interact with OpenAI models directly through the gateway!
  - Example endpoint: `/api.openai.com/v1/chat/completions`.
  - Parser added for OpenAI token usage tracking.
- 📦 **Gzip Encoding Support**: Added gzip decoding for upstream responses.
  - Handles gzip-encoded responses from upstream services seamlessly.
  - Ensures efficient data transfer and processing.
- ⚙️ **Admin Service Configuration**: Added admin host/port configuration to server config.
  - Admin service now uses configurable values instead of hardcoded ones.
  - Improved flexibility for deployment environments.
- 🤖 **CI/CD Pipeline**: Set up GitHub Actions for continuous integration.
  - Added workflows for building, testing, and releasing Rust binaries.
  - Supports multiple platforms: Linux (x86_64, arm64) and macOS.
---
### 🛠️ **Bug Fixes & Improvements**
- 🔒 **Token Validation**: Improved token validation in the admin interface.
  - Tokens shorter than 32 characters are now rejected.
  - Better error handling for invalid JSON requests.
- 📄 **Response Header Handling**: Fixed response header handling in the gateway.
  - Removed hardcoded headers and improved content encoding management.
  - Ensures proper handling of `Transfer-Encoding` and `Content-Length`.
- 🕵️ **PII Protection**: Enhanced PII (Personally Identifiable Information) detection.
  - Added tests for long text inputs with PII.
  - Improved handling of blacklisted words and confidential data.
- 📊 **Echo Service**: Renamed request counter for clarity.
  - Changed `REQ_COUNTER` to `ECHO_REQ_COUNTER` for better readability.
---
### 🧪 **Tests & Quality Assurance**
- 🧑‍💻 **Admin Interface Tests**: Added comprehensive tests for the admin interface.
  - Covers token creation, deletion, and usage stats.
  - Includes edge cases like invalid JSON and timeout handling.
- 📝 **Local Tests**: Added local tests for PII and long text handling.
  - Ensures proper detection of PII in large inputs.
  - Validates blacklisted word filtering.
- 🌐 **Remote Tests**: Expanded remote tests for Deepseek and OpenAI APIs.
  - Added test cases for OpenAI API integration.
  - Improved Deepseek API test coverage.
---
### 📚 **Configuration & Documentation**
- 🖥️ **Config Updates**: Updated `conf.yml` with new admin host/port settings.
  - Added `admin_host` and `admin_port` configurations.
  - Improved proxy pass and model configurations.
- 📜 **Changelog Updates**: Updated the changelog with recent changes.
  - Added details about new features, bug fixes, and tests.
---
### 🎉 **Miscellaneous**
- 📂 **File Renaming**: Renamed `changelog.md` to `CHANGELOG.md` for consistency.
- 🔄 **Dependency Updates**: Added `flate2` crate for gzip support.


## [0.1.1] - 2025-01-23

### Added
- ✅ Support to OpenAI API
- 🔧 Manage upstream content encoding with gzip
- 🛠️ Continuous integration with GitHub Actions


## [0.1.0] - 2025-01-22

### Added
- 🛠️ Complete Rust migration for improved performance and safety
- 🚪 New admin service with web UI for configuration and monitoring
- 📊 Prometheus metrics integration for real-time monitoring
- 🔑 Token management system with quotas and rate limiting
- 🤖 Support for multiple LLM providers (OpenAI, Claude, DeepSeek, Ollama)
- 🔒 PII detection and content filtering capabilities

### Changed
- 📄 Complete documentation overhaul with new guides and API references
- 🔄 Refactored rate limiting system for better scalability
- 🛡️ Enhanced security with trusted header authentication

### Removed
- 🗑️ Legacy Python implementation
- 🚫 Deprecated configuration options

---

*This project follows [Semantic Versioning](https://semver.org/)*

