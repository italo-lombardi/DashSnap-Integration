# Changelog

All notable changes to DashSnap Integration.

## [Unreleased]

### Fixed
- `lang` service field `name`/`description` now carry real native translations in the 27 affected non-English files — 0.1.1 shipped the English source text pasted verbatim (de.json already held correct German)
- Translation test now fails if any leaf value is identical to English across every language, so an untranslated paste can no longer pass review

## [0.1.1] - 2026-10-29

### Added
- `lang` parameter on both services (e.g. `lang: de`) — forwarded to DashSnap ≥ 0.1.15, which sets the browser locale and the HA frontend language for the capture
- Translations for 18 languages: zh-Hans, zh-Hant, ru, ja, ko, uk, cs, sk, hu, ro, bg, hr, fi, el, tr, lt, lv, ca — reaching the full HA core coverage target (~29 languages total)

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
