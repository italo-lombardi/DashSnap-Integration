# Changelog

All notable changes to DashSnap Integration.

## [0.0.2] - 2026-07-15

### Fixed
- `aiohttp.ClientTimeout` used for all HTTP calls — bare int timeout caused `ClientConnectionResetError` on recordings longer than the implicit default
- Service field descriptions: removed personal site references, expanded `target` field to explain what targets are and how to find them

### Changed
- Removed `CONF_TARGETS` — target details are DashSnap's concern; integration only stores `base_url`. Services pass the `target` name directly through to DashSnap.

## [0.0.1] - 2026-07-14

Initial release.

### Features

- **`dashsnap.record_ha`** — record a Home Assistant page by path; base URL applied automatically from DashSnap target config.
- **`dashsnap.record`** — record any full URL (Grafana, public pages, anything with a full `http://` / `https://` URL).
- **Auto-detection** — config flow probes common DashSnap URLs (Supervisor add-on, Docker Compose, localhost); pre-fills and creates entry if found.
- **Multi-target** — optional `target` parameter selects a named DashSnap target; fetched and cached from `/targets` on setup.
- **Response support** — both services return `{"ok": true, "file": "..."}` for use in script `response_variable`.
- **Options flow** — update the DashSnap base URL without reinstalling; health-checked before saving.
- **11 locales** — config/options UI translated in da, de, en, es, fr, it, nb, nl, pl, pt, sv.
- **100% test coverage** — pytest with pytest-homeassistant-custom-component.
