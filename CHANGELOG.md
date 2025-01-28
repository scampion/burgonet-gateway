# Changelog

## [0.1.3] - 2025-01-24


#### 🛠️ **Code Improvements & Bug Fixes**

- **Audit Log Rotation** 🔄
  - Updated the audit log configuration (`log4rs.yml`) to support rotating logs based on size (50MB limit) and date.
  - Added a fixed-window roller to maintain up to 5 archived log files.
  - Ensured logs are stored persistently with configurable retention periods.
- **Error Handling in Audit Logs** 🚨
  - Added error logging for responses with HTTP status codes >= 400 in `gateway.rs`.
  - Improved request logging by removing newline characters for cleaner audit logs.
- **Configuration File Handling** ⚙️
  - Fixed an issue in `main.rs` where the program would not exit properly when no configuration file was provided.
  - Removed redundant `env_logger::init()` call and added a proper error message.

---

#### 📚 **Documentation Updates**

- **Features Documentation** 📝
  - Added a new section in the documentation (`mkdocs.yml`) to detail the Features of the gateway, including audit logs and storage.
- **README.md Updates** 📖
  - Added descriptions for Audit Logs and Audit Storage features in the README.

---

#### 🚀 **New Features**

- **Audit Log Enhancements** 📋
  - Introduced detailed logging of API requests and responses in `gateway.rs`.
  - Added persistent storage for all gateway exchanges with configurable retention periods.

---

#### 🧹 **Code Cleanup**

- Removed redundant code and improved readability in `gateway.rs` and `main.rs`.


## [0.1.2] - 2025-01-23

### 🛠️ **Fixes**
- **JSON Handling**:
  - Fixed JSON escaping by replacing manual handling with `jq` for proper character handling. (`024c6f0`)
  - Sanitized `ACTIVITY_CONTENT` for JSON by escaping special characters. (`a6dc37d`)
- **CORS Improvements**:
  - Added CORS preflight request handling in the gateway. (`f1d1d94`)
  - Removed `no-cors` mode and enhanced CORS headers for proper response handling. (`c210d41`)
- **Code Cleanup**:
  - Simplified parser assignment and removed redundant code in `chat.html`. (`1949cd2`)
  - Simplified configuration handling and response filtering in the gateway. (`4d3dd85`)
- **Miscellaneous Fixes**:
  - Various fixes applied. (`f81fa3e`)

### ✨ **Features**
- **Automation**:
  - Added `activity4changelog.sh` script to automate changelog generation. (`11283a4`)
- **Chat Service Enhancements**:
  - Added chat service with conversation management endpoints. (`a2409c0`)
  - Delegated chat API handling to the admin module. (`1c74add`)
  - Added default host and port configurations for chat and echo services. (`bfb6610`, `815cf9b`)
- **UI/UX Improvements**:
  - Added a save button to the navbar for explicit conversation saving. (`fdc1b63`)
  - Displayed individual conversation items in the sidebar with previews. (`d5691c5`)
  - Made the navbar fixed and full-width with proper content spacing. (`ed9cc13`)
  - Added Enter key message sending with Shift+Enter for new lines. (`569ed9c`)
  - Added model selection dropdown to the chat interface. (`7d49b8b`)
- **API Enhancements**:
  - Updated model selection to handle new API response format. (`7bab77f`)
  - Added model-specific message parsers in `parsers.js`. (`3ae29f0`)
  - Added `Authorization` header with bearer token to API requests. (`3477fb4`)
  - Dynamically populated `model-select` from gateway endpoint. (`e3b5028`)
- **Configuration**:
  - Handled root path requests by returning configuration in JSON format. (`e80b498`)
  - Added early return for root and login paths with YAML config. (`e1fdf62`)

### 📚 **Documentation**
- Added chat interface documentation and navigation. (`11283a4`)

### 🔄 **Refactors**
- **Code Simplification**:
  - Used composition to delegate common functionality to `HttpAdminApp`. (`a2408a8`)
  - Simplified error messages in `chat.html`. (`113168e`)
  - Simplified request handling and moved root path logic to response filter. (`0eece05`)
- **UI Refactoring**:
  - Moved inline styles to external CSS and adjusted navbar layout. (`1456084`)
  - Replaced navbar links with server URL input in `chat.html`. (`41c5eba`)

### 🧹 **Chores**
- Updated `proxy_pass` URL in `conf.yml` to use port 6193. (`159f612`)
- Added service declaration route for the `/` URI to display all available models. (`d1830be`)

### 🎨 **Styling**
- **UI Adjustments**:
  - Adjusted `model-select` margin for left alignment. (`a997bbb`)
  - Aligned `model-select` to the left in `input-form` and adjusted spacing. (`a6fcbcd`)
  - Adjusted widths for `#model-select` and `#send-button` elements. (`ebdaf30`)
  - Adjusted form element widths and spacing in `input-form`. (`701f135`)
  - Adjusted navbar image margin and chat container alignment. (`29a7263`)
- **Color & Layout**:
  - Updated chat interface colors for better readability. (`b23df74`)
  - Commented out height calculation in CSS. (`689ee22`)

### ✨ **New Features & Enhancements**
- **OpenAI API Integration**:
  - Added support for OpenAI API integration.
  - Example endpoint: `/api.openai.com/v1/chat/completions`.
  - Parser added for OpenAI token usage tracking.
- **Gzip Encoding Support**:
  - Added gzip decoding for upstream responses.
  - Ensures efficient data transfer and processing.
- **Admin Service Configuration**:
  - Added admin host/port configuration to server config.
  - Improved flexibility for deployment environments.
- **CI/CD Pipeline**:
  - Set up GitHub Actions for continuous integration.
  - Added workflows for building, testing, and releasing Rust binaries.
  - Supports multiple platforms: Linux (x86_64, arm64) and macOS.

### 🛠️ **Bug Fixes & Improvements**
- **Token Validation**:
  - Improved token validation in the admin interface.
  - Tokens shorter than 32 characters are now rejected.
- **Response Header Handling**:
  - Fixed response header handling in the gateway.
  - Removed hardcoded headers and improved content encoding management.
- **PII Protection**:
  - Enhanced PII (Personally Identifiable Information) detection.
  - Added tests for long text inputs with PII.
- **Echo Service**:
  - Renamed request counter for clarity (`REQ_COUNTER` to `ECHO_REQ_COUNTER`).

### 🧪 **Tests & Quality Assurance**
- **Admin Interface Tests**:
  - Added comprehensive tests for token creation, deletion, and usage stats.
- **Local Tests**:
  - Added local tests for PII and long text handling.
- **Remote Tests**:
  - Expanded remote tests for Deepseek and OpenAI APIs.

### 📚 **Configuration & Documentation**
- **Config Updates**:
  - Updated `conf.yml` with new admin host/port settings.
- **Changelog Updates**:
  - Added details about new features, bug fixes, and tests.

### 🎉 **Miscellaneous**
- Renamed `changelog.md` to `CHANGELOG.md` for consistency.
- Added `flate2` crate for gzip support.

---


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

