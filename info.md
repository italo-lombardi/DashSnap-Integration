# DashSnap Integration for Home Assistant

Trigger web page recordings and screenshots from HA automations and scripts via [DashSnap](https://github.com/italo-lombardi/DashSnap).

## Services

- **`dashsnap.record_ha`** — record a Home Assistant page by path (base URL auto-applied from DashSnap target config)
- **`dashsnap.record`** — record any full URL (Grafana, public pages, anything)

Both services accept optional `target`, `seconds`, `format`, `viewport_width`, `viewport_height` parameters and return the saved file path.

## Setup

1. Install and start DashSnap (HA App or Docker).
2. Add this integration — DashSnap is auto-detected if reachable.
3. Use `dashsnap.record_ha` or `dashsnap.record` in automations and scripts.
