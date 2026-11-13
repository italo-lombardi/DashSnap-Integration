# Changelog

All notable changes to DashSnap Integration.

## [Unreleased]

## [0.1.5] - 2026-11-13

### Fixed
- Service calls no longer block for the full 15-minute record timeout when the DashSnap app is wedged. A `sock_connect` cap (10s) is now applied alongside the long total timeout, so a renderer whose socket is still listening but whose app has hung fails the connect phase quickly, triggering auto-recovery instead of stalling the caller. The long total is preserved so a legitimately long capture still completes once connected.
- A non-dict JSON body on an otherwise-successful (HTTP 200) response is now handled gracefully instead of raising a raw `AttributeError`. A stale IP that is reclaimed by a different service and answers `200` with `null`, a list, or a scalar previously crashed the service call with an uncaught traceback and no recovery; the record/list/delete paths now surface a clean "could not reach DashSnap" error, and the config/recovery health probe treats such a response as unhealthy and continues to the next candidate.

## [0.1.4] - 2026-11-09

### Fixed
- Auto-recovery now resolves the app's current container IP from the Supervisor API (`/addons/{slug}/info` → `ip_address`) instead of the app hostname. On Home Assistant OS the app hostname does not resolve from HA Core, so after a container restart changed the app's IP, recovery previously found no reachable candidate and every service call failed with `Could not reach DashSnap` until the base URL was edited by hand. Recovery now re-pins the live IP automatically on the next call.
- Auto-recovery now also triggers on `ClientResponseError` (e.g. a stale IP that now answers with a bogus HTTP response — `0, message=''`), not only connection-refused/reset errors. Previously that response slipped past the recovery catch and raised immediately, so the self-heal never ran.

### Added
- When a DashSnap service call cannot reach the app (and auto-recovery either fails or does not apply), a persistent notification is raised (so failures from scripts/automations, which otherwise only hit the logbook, are visible). If the Supervisor reports the DashSnap app is stopped, the message says so and points to Settings → Apps → DashSnap.

### Changed
- If automatic recovery still cannot reach DashSnap (e.g. Supervisor unavailable, or DashSnap running on host/bridge networking with no assigned IP), update the base URL manually in the integration's **Configure** dialog. The app's current IP is shown in **Settings → Apps → DashSnap** on its info page.

## [0.1.3] - 2026-11-08

### Added
- `list_recordings` service — lists recordings stored by DashSnap (name, size, capture time, format, slug), with optional `format`, `slug`, and `older_than_days` filters. Returns a response (read-only).
- `delete_recordings` service — deletes recordings by `name` (exact filename), `slug` (target), `older_than_days` (retention, by capture timestamp), or `delete_all`; optional `format` filter and `dry_run` preview. Refuses a filterless call unless `delete_all` is set. Requires DashSnap addon ≥ 0.1.17 (`GET /recordings`, `POST /recordings/delete`).
- Native translations of both new services for all 29 languages.

### Security
- Service inputs are validated at the HA trust boundary before any request: filename against `^\d{8}_\d{6}_[A-Za-z0-9_]{1,40}\.(?:webm|png)$`, slug against `^[A-Za-z0-9_]{1,40}$`, `older_than_days` as a non-negative integer, `format` as an enum. The addon independently re-guards path containment and the recording-name allowlist.

## [0.1.2] - 2026-10-30

### Fixed
- `lang` service field `name`/`description` now carry real native translations in the 27 affected non-English files — 0.1.1 shipped the English source text pasted verbatim (de.json already held correct German)
- Translation test now fails if any file matches English above a 50% leaf ratio, so an untranslated paste (even a single file) can no longer pass review

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
