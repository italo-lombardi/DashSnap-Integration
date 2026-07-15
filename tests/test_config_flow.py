"""Tests for DashSnap config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dashsnap.const import CONF_BASE_URL, DOMAIN

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GOOD_URL = "http://dashsnap:8099"


def _ok_resp(json_data: dict):
    """Successful response context manager."""
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value=json_data)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=resp)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _raising_cm(exc=None):
    """Context manager that raises on __aenter__."""
    if exc is None:
        exc = Exception("timeout")
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(side_effect=exc)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _session_raises():
    """Session where every .get() raises."""
    session = MagicMock()
    session.get = MagicMock(return_value=_raising_cm())
    return session


def _session_health_ok_targets():
    """Session: /health → ok=True, /targets → list, others → raises."""
    session = MagicMock()

    def _get(url, **kwargs):
        if "/health" in url:
            return _ok_resp({"ok": True})
        if "/targets" in url:
            return _ok_resp({"ok": True, "targets": [{"name": "ha", "strategy": "ha_token"}]})
        return _raising_cm()

    session.get = _get
    return session


def _session_health_unhealthy():
    """Session: /health returns ok=False (reachable but unhealthy)."""
    session = MagicMock()

    def _get(url, **kwargs):
        if "/health" in url:
            return _ok_resp({"ok": False})
        return _raising_cm()

    session.get = _get
    return session


# ---------------------------------------------------------------------------
# Config flow — autodetect succeeds
# ---------------------------------------------------------------------------


async def test_autodetect_creates_entry_directly(hass: HomeAssistant):
    """When autodetect probe succeeds, entry is created without showing form."""
    with (
        patch(
            "custom_components.dashsnap.config_flow.async_get_clientsession",
            return_value=_session_health_ok_targets(),
        ),
        patch.dict("os.environ", {}, clear=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_BASE_URL] == _GOOD_URL


# ---------------------------------------------------------------------------
# Config flow — autodetect fails → form shown
# ---------------------------------------------------------------------------


async def test_user_step_shows_form_when_autodetect_fails(hass: HomeAssistant):
    with (
        patch(
            "custom_components.dashsnap.config_flow.async_get_clientsession",
            return_value=_session_raises(),
        ),
        patch.dict("os.environ", {}, clear=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_user_step_creates_entry_on_valid_url(hass: HomeAssistant):
    """Autodetect fails → user submits valid URL → entry created."""
    with (
        patch(
            "custom_components.dashsnap.config_flow.async_get_clientsession",
            return_value=_session_raises(),
        ) as mock_cls,
        patch.dict("os.environ", {}, clear=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        # Now switch the session mock to a healthy one
        mock_cls.return_value = _session_health_ok_targets()
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_BASE_URL: _GOOD_URL}
        )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_BASE_URL] == _GOOD_URL


async def test_user_step_error_invalid_url(hass: HomeAssistant):
    with (
        patch(
            "custom_components.dashsnap.config_flow.async_get_clientsession",
            return_value=_session_raises(),
        ),
        patch.dict("os.environ", {}, clear=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_BASE_URL: "not-a-url"}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_url"


async def test_user_step_error_cannot_connect(hass: HomeAssistant):
    with (
        patch(
            "custom_components.dashsnap.config_flow.async_get_clientsession",
            return_value=_session_raises(),
        ),
        patch.dict("os.environ", {}, clear=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_BASE_URL: _GOOD_URL}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_user_step_error_app_unhealthy(hass: HomeAssistant):
    with (
        patch(
            "custom_components.dashsnap.config_flow.async_get_clientsession",
            return_value=_session_raises(),
        ) as mock_cls,
        patch.dict("os.environ", {}, clear=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        mock_cls.return_value = _session_health_unhealthy()
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_BASE_URL: _GOOD_URL}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "app_unhealthy"


async def test_user_step_abort_already_configured(hass: HomeAssistant):
    existing = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="DashSnap",
        data={CONF_BASE_URL: _GOOD_URL},
        unique_id=DOMAIN,
    )
    existing.add_to_hass(hass)

    with (
        patch(
            "custom_components.dashsnap.config_flow.async_get_clientsession",
            return_value=_session_raises(),
        ) as mock_cls,
        patch.dict("os.environ", {}, clear=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        mock_cls.return_value = _session_health_ok_targets()
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_BASE_URL: _GOOD_URL}
        )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# ---------------------------------------------------------------------------
# Supervisor autodetect paths
# ---------------------------------------------------------------------------


async def test_autodetect_via_supervisor_addon(hass: HomeAssistant):
    session = MagicMock()

    def _get(url, **kwargs):
        if "/addons" in url:
            return _ok_resp(
                {
                    "data": {
                        "addons": [{"slug": "c1b14015_dashsnap", "hostname": "c1b14015-dashsnap"}]
                    }
                }
            )
        if "/health" in url:
            return _ok_resp({"ok": True})
        if "/targets" in url:
            return _ok_resp({"ok": True, "targets": [{"name": "ha", "strategy": "ha_token"}]})
        return _raising_cm()

    session.get = _get

    with (
        patch(
            "custom_components.dashsnap.config_flow.async_get_clientsession", return_value=session
        ),
        patch.dict("os.environ", {"SUPERVISOR_TOKEN": "fake-token"}),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert "c1b14015-dashsnap" in result["data"][CONF_BASE_URL]


async def test_autodetect_supervisor_no_hostname_uses_slug(hass: HomeAssistant):
    """Addon without hostname → slug used as fallback."""
    session = MagicMock()

    def _get(url, **kwargs):
        if "/addons" in url:
            return _ok_resp({"data": {"addons": [{"slug": "dashsnap_app"}]}})
        if "/health" in url:
            return _ok_resp({"ok": True})
        if "/targets" in url:
            return _ok_resp({"ok": True, "targets": []})
        return _raising_cm()

    session.get = _get

    with (
        patch(
            "custom_components.dashsnap.config_flow.async_get_clientsession", return_value=session
        ),
        patch.dict("os.environ", {"SUPERVISOR_TOKEN": "fake-token"}),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert "dashsnap_app" in result["data"][CONF_BASE_URL]


async def test_autodetect_supervisor_no_dashsnap_slug_falls_through(hass: HomeAssistant):
    """Supervisor returns addons but none match 'dashsnap' → fall through to probes."""
    session = MagicMock()

    def _get(url, **kwargs):
        if "/addons" in url:
            return _ok_resp({"data": {"addons": [{"slug": "other_addon"}]}})
        return _raising_cm()

    session.get = _get

    with (
        patch(
            "custom_components.dashsnap.config_flow.async_get_clientsession", return_value=session
        ),
        patch.dict("os.environ", {"SUPERVISOR_TOKEN": "fake-token"}),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] == FlowResultType.FORM


async def test_autodetect_supervisor_exception_falls_through(hass: HomeAssistant):
    """Supervisor /addons raises → fall through to probes."""
    session = MagicMock()
    session.get = MagicMock(return_value=_raising_cm())

    with (
        patch(
            "custom_components.dashsnap.config_flow.async_get_clientsession", return_value=session
        ),
        patch.dict("os.environ", {"SUPERVISOR_TOKEN": "fake-token"}),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] == FlowResultType.FORM


# ---------------------------------------------------------------------------
# _fetch_targets edge cases
# ---------------------------------------------------------------------------


async def test_fetch_targets_exception_returns_empty(hass: HomeAssistant):
    """Targets fetch raises → stored as [] and entry still created."""
    session = MagicMock()

    def _get(url, **kwargs):
        if "/health" in url:
            return _ok_resp({"ok": True})
        # /targets raises
        return _raising_cm()

    session.get = _get

    with (
        patch(
            "custom_components.dashsnap.config_flow.async_get_clientsession", return_value=session
        ),
        patch.dict("os.environ", {}, clear=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] == FlowResultType.CREATE_ENTRY


# ---------------------------------------------------------------------------
# Options flow
# ---------------------------------------------------------------------------


async def test_options_flow_shows_form(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    mock_config_entry.add_to_hass(hass)
    with patch("custom_components.dashsnap.services.async_register_services"):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_updates_base_url(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    mock_config_entry.add_to_hass(hass)
    with patch("custom_components.dashsnap.services.async_register_services"):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    with patch(
        "custom_components.dashsnap.config_flow.async_get_clientsession",
        return_value=_session_health_ok_targets(),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_BASE_URL: "http://new:8099"}
        )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_BASE_URL] == "http://new:8099"


async def test_options_flow_invalid_url_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    mock_config_entry.add_to_hass(hass)
    with patch("custom_components.dashsnap.services.async_register_services"):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_BASE_URL: "bad"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_url"


async def test_options_flow_cannot_connect(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    mock_config_entry.add_to_hass(hass)
    with patch("custom_components.dashsnap.services.async_register_services"):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    with patch(
        "custom_components.dashsnap.config_flow.async_get_clientsession",
        return_value=_session_raises(),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_BASE_URL: _GOOD_URL}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_options_flow_app_unhealthy(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    mock_config_entry.add_to_hass(hass)
    with patch("custom_components.dashsnap.services.async_register_services"):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    with patch(
        "custom_components.dashsnap.config_flow.async_get_clientsession",
        return_value=_session_health_unhealthy(),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_BASE_URL: _GOOD_URL}
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "app_unhealthy"
