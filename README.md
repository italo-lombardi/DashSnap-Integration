# DashSnap Integration for Home Assistant

<a href="https://github.com/italo-lombardi/DashSnap-Integration/releases"><img src="https://img.shields.io/github/v/release/italo-lombardi/DashSnap-Integration" alt="GitHub Release"></a>
<a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
<a href="https://github.com/italo-lombardi/DashSnap-Integration"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json&query=%24.dashsnap.total&label=installs&color=41BDF5" alt="HACS Installs"></a>
<a href="https://www.home-assistant.io/"><img src="https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg" alt="Home Assistant"></a>
<a href="https://github.com/italo-lombardi/DashSnap-Integration/blob/main/LICENSE"><img src="https://img.shields.io/github/license/italo-lombardi/DashSnap-Integration?logo=gnu&logoColor=white" alt="License"></a>
<img src="https://img.shields.io/badge/coverage-100%25-brightgreen" alt="Test Coverage">
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/italolombardi)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=flat&logo=paypal&logoColor=white)](https://paypal.me/ItaloLombardi)

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=italo-lombardi&repository=DashSnap-Integration&category=integration)
[![Add to Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=dashsnap)

Home Assistant integration for [DashSnap](https://github.com/italo-lombardi/DashSnap) — trigger web page recordings and screenshots from HA automations and scripts.

DashSnap is a headless Chromium recorder that captures any URL to `.webm` video or `.png` screenshot. This integration connects HA to a running DashSnap instance (HA App, Docker, or Docker Compose) and exposes two services for use in automations.

---

## Features

- **`dashsnap.record_ha`** — record a Home Assistant page by path; the base URL is resolved automatically from the DashSnap target config
- **`dashsnap.record`** — record any full URL (Grafana, public pages, anything)
- **Auto-detection** — finds a local DashSnap instance automatically on setup using `self_urls` from `/health`; self-heals if the addon IP changes after a container restart
- **Multi-target** — pass an optional `target` name to select which DashSnap target to use
- **Returns the output file path** from both services (usable in scripts and automations)

---

## Requirements

DashSnap must be running and reachable from Home Assistant. Install options:

| Method | Docs |
|--------|------|
| **HA App (Supervisor)** | [DashSnap repo](https://github.com/italo-lombardi/DashSnap) — add the repository and install |
| **Docker Compose** | See [docker-compose.yml](https://github.com/italo-lombardi/DashSnap/blob/main/docker-compose.yml) |
| **Docker standalone** | `docker run -p 8099:8099 -v /media:/media ghcr.io/italo-lombardi/dashsnap` |

---

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations** and click the three-dot menu.
3. Select **Custom repositories**.
4. Add `https://github.com/italo-lombardi/DashSnap-Integration` with category **Integration**.
5. Click **Install** and restart Home Assistant.

### Manual

1. Download the [latest release](https://github.com/italo-lombardi/DashSnap-Integration/releases).
2. Copy the `custom_components/dashsnap/` folder into your `config/custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration

![Config flow — add integration](assets/00_add_integration.png)

Go to **Settings → Devices & Services → Add Integration → DashSnap**.

The integration auto-detects a running DashSnap instance on the local network. If found, it is pre-configured and the entry is created automatically. Otherwise, enter the base URL manually.

| Field | Description | Example |
|-------|-------------|---------|
| DashSnap base URL | URL where DashSnap is reachable from HA | `http://dashsnap:8099` |

**Common base URLs:**

| Deployment | URL |
|------------|-----|
| HA App (Supervisor) | `http://<addon-hostname>:8099` (auto-detected) |
| Docker Compose (same network) | `http://dashsnap:8099` |
| Docker on host | `http://host.docker.internal:8099` |
| LAN IP | `http://192.168.1.50:8099` |

---

## Services

![Services in HA developer tools](assets/01_services.png)

### `dashsnap.record_ha`

Record a Home Assistant page by path. The HA base URL is applied automatically from the DashSnap target configuration — you only need the path.

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `path` | ✅ | — | HA route to capture, e.g. `/lovelace/0` |
| `target` | ✗ | first target | Named DashSnap target (e.g. `ha`) |
| `seconds` | ✗ | 30 | Video duration (ignored for `png`) |
| `delay` | ✗ | 0 | Seconds to wait for page to settle before recording starts |
| `format` | ✗ | `webm` | `webm` or `png` |
| `viewport_width` | ✗ | 1920 | Render width in pixels |
| `viewport_height` | ✗ | 1080 | Render height in pixels |

### `dashsnap.record`

Record any web page by full URL.

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `url` | ✅ | — | Full URL to capture |
| `target` | ✗ | first target | Named DashSnap target |
| `seconds` | ✗ | 30 | Video duration (ignored for `png`) |
| `delay` | ✗ | 0 | Seconds to wait for page to settle before recording starts |
| `format` | ✗ | `webm` | `webm` or `png` |
| `viewport_width` | ✗ | 1920 | Render width in pixels |
| `viewport_height` | ✗ | 1080 | Render height in pixels |

---

## Automation Examples

### Screenshot a dashboard on a schedule

```yaml
automation:
  - alias: Daily dashboard snapshot
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: dashsnap.record_ha
        data:
          path: /lovelace/0
          format: png
          target: ha
```

### Record a public page for 10 seconds

```yaml
automation:
  - alias: Record Infoshare on demand
    trigger:
      - platform: state
        entity_id: input_boolean.record_now
        to: "on"
    action:
      - service: dashsnap.record
        data:
          url: https://www.infoshare.it
          seconds: 10
          format: webm
          target: public
```

### Use the returned file path

```yaml
script:
  capture_and_notify:
    sequence:
      - service: dashsnap.record_ha
        data:
          path: /lovelace/0
          format: png
        response_variable: snap
      - service: notify.mobile_app_iphone
        data:
          message: "Snapshot saved: {{ snap.file }}"
```

---

## Multi-target Setup

DashSnap supports multiple named targets (HA, Grafana, public pages) configured in its `options.json` / `targets_json` field. When calling a service, pass the `target` name to select which one to use.

Call `GET http://<dashsnap-url>:8099/targets` to list configured targets.

---

> This is an unofficial integration not affiliated with Home Assistant.
