# Changelog

All notable changes to DashSnap Integration.

## [0.1.0] - 2026-07-16

### Added
- Auto-detection uses `self_urls` from DashSnap `/health` — integration picks up the correct internal addon address automatically
- Self-healing URL retry: if the addon IP changes (container restart, supervisor migration), the integration re-probes and updates the stored URL transparently
- `delay` parameter on both services — seconds to wait for the page to settle before recording starts

### Fixed
- `aiohttp.ClientTimeout` used for all HTTP calls — bare int timeout caused `ClientConnectionResetError` on long recordings
- Slug hostname fix: `_` → `-` for correct HA Supervisor DNS resolution

### Changed
- Removed `CONF_TARGETS` — target details are DashSnap's concern; integration only stores `base_url`
- `localhost` and `homeassistant.local` removed from probe candidates — neither is reachable from inside a container
