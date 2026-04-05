# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-04-05
### Fixed
- Fixed build error by replacing deprecated `homeassistant_api`/`hassio_api` with `ingress` config
- Improved security with proper MIME type checking (python-magic)
- Added rate limiting to login endpoint (slowapi)
- Added upload file size limits (25MB)
- Removed default plain-text password from config
- Added path traversal protection in config schema
- Cleaned up duplicate requirements

## [1.0.0] - 2026-04-05
### Added
- Initial release
- Beautiful user interface based on Midnight Slate design
- Drag & Drop photo upload
- Gallery management (view and delete photos)
- Home Assistant Media folder integration
- Home Assistant persistent notifications on successful upload
- Password protection with rate limiting
- File size and MIME type validation
