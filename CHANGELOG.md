# Changelog

All notable changes to Forest Comms.

## [2.3.0] - 2026-02-06

### Added
- **File upload support** — `POST /api/upload` endpoint, `GET /api/files/{name}` serving
- Attachments field on messages with metadata (filename, size, URL)
- Paperclip button in UI for file selection
- Pending files bar with remove capability
- Inline image previews for uploaded images (jpg, png, gif, webp, svg)
- Download links with file icon and size display for non-image files
- 25MB per-file upload limit

## [2.2.0] - 2026-02-06

### Added
- **Copy button** on every message bubble — click to copy message text
- "Copied!" flash feedback with green accent

## [2.1.0] - 2026-02-06

### Added
- **BigC user identity** — purple avatar and bubble theme for Claude (claude.ai)
- BigC added to From/To dropdowns in UI
- Professional documentation suite (README, ARCHITECTURE, API reference, CHANGELOG)

### Changed
- Header subtitle updated to include BigC

## [2.0.0] - 2026-02-06

### Added
- **Per-bot delivery tracking** — `delivered_to: {"cypress": true, "redwood": false}` replaces global boolean
- **Claude-style web UI** — complete redesign with dark forest theme
- Grouped message bubbles by sender with colored circular avatars
- Auto-expanding textarea with Shift+Enter for newlines
- Auto-scroll with smart detection (won't jump if user scrolled up)
- CC mirroring: bot-to-bot messages automatically copied to Matthew
- Webhook wake system for both Cypress and Redwood agents
- Health endpoint at `/health`

### Fixed
- **Critical bug**: `to="all"` messages only delivered to first bot that polled (global `delivered` boolean)

### Changed
- Default port changed to 5001
- Bridge default URL updated to port 5001

## [1.0.0] - 2026-02-03

### Added
- Initial Forest Chat hub with Flask API
- Basic message send/receive endpoints
- Simple HTML UI
- Cypress bridge via OpenClaw webhooks
- CDP-based BigC communication tools (`cypress/bigc_cdp.py`)
- BigC → Cypress relay skill (`bigc/cypress-relay/`)
