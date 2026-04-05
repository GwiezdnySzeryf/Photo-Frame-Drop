# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.7] - 2026-04-05
### Fixed
- Fixed runtime crash `RuntimeError: Directory 'static' does not exist` by ensuring the `static` directory is tracked by Git using a `.keep` file.

## [1.0.6] - 2026-04-05
### Fixed
- Removed raw `ports` configuration to fix conflicts with `ingress` which was causing unknown build errors in Supervisor on modern HA versions.

## [1.0.5] - 2026-04-05
### Fixed
- Fixed `pip: not found` error during build by using `pip3` instead of `pip` (Alpine's `py3-pip` package uses `pip3` alias).

## [1.0.4] - 2026-04-05
### Fixed
- Fixed build error caused by Supervisor overriding the `BUILD_FROM` argument. Explicitly installed `python3` and `py3-pip` in the Dockerfile.
- Added `--break-system-packages` to `pip install` to support newer Alpine versions (PEP 668).

## [1.0.3] - 2026-04-05
### Fixed
- Updated base image to `ghcr.io/hassio-addons/base-python:18.0.0`
- Reverted to `python-magic` and fixed Alpine C-dependencies by adding `file` package alongside `libmagic`.
- Optimized Dockerfile to use `pip` alias from newer base image.

## [1.0.2] - 2026-04-05
### Fixed
- Fixed Docker image build errors on ARM architectures by removing `pillow` dependency (not used for core functionality).
- Replaced `python-magic` (requires C-libraries) with pure-python `filetype` to ensure cross-platform compatibility.

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
