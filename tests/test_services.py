"""Tests for DashSnap services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dashsnap.const import (
    ATTR_DELAY,
    ATTR_FORMAT,
    ATTR_PATH,
    ATTR_SECONDS,
    ATTR_TARGET,
    ATTR_URL,
    ATTR_VIEWPORT_HEIGHT,
    ATTR_VIEWPORT_WIDTH,
    CONF_BASE_URL,
    DOMAIN,
    SERVICE_RECORD,
    SERVICE_RECORD_HA,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_post_resp(ok: bool = True, file: str = "/media/dashsnap/page.webm"):
    resp = AsyncMock()
    data = {"ok": ok, "file": file} if ok else {"ok": False, "error": "boom"}
    resp.json = AsyncMock(return_value=data)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=resp)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _patched_session(ok: bool = True):
    session = MagicMock()
    session.post = MagicMock(return_value=_mock_post_resp(ok=ok))
    return session


async def _setup_integration(hass: HomeAssistant, base_url: str = "http://dashsnap:8099"):
    entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="DashSnap",
        data={CONF_BASE_URL: base_url},
        entry_id="svc_entry",
        unique_id=DOMAIN + "_svc",
    )
    entry.add_to_hass(hass)
    with patch("custom_components.dashsnap.config_flow.async_get_clientsession"):
        await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


# ---------------------------------------------------------------------------
# _base_url
# ---------------------------------------------------------------------------


async def test_base_url_raises_when_not_configured(hass: HomeAssistant):
    from custom_components.dashsnap.services import _base_url

    with pytest.raises(HomeAssistantError, match="not configured"):
        _base_url(hass)


async def test_base_url_strips_trailing_slash(hass: HomeAssistant):
    await _setup_integration(hass, base_url="http://dashsnap:8099/")
    from custom_components.dashsnap.services import _base_url

    assert _base_url(hass) == "http://dashsnap:8099"


# ---------------------------------------------------------------------------
# register / unregister
# ---------------------------------------------------------------------------


async def test_services_registered_after_setup(hass: HomeAssistant):
    await _setup_integration(hass)
    assert hass.services.has_service(DOMAIN, SERVICE_RECORD)
    assert hass.services.has_service(DOMAIN, SERVICE_RECORD_HA)


async def test_services_not_double_registered(hass: HomeAssistant):
    await _setup_integration(hass)
    # Call register again — should be idempotent
    from custom_components.dashsnap.services import async_register_services

    async_register_services(hass)
    assert hass.services.has_service(DOMAIN, SERVICE_RECORD)


async def test_services_unregistered_on_unload(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    assert not hass.services.has_service(DOMAIN, SERVICE_RECORD)
    assert not hass.services.has_service(DOMAIN, SERVICE_RECORD_HA)


# ---------------------------------------------------------------------------
# handle_record
# ---------------------------------------------------------------------------


async def test_handle_record_success(hass: HomeAssistant):
    await _setup_integration(hass)
    with patch(
        "custom_components.dashsnap.services.async_get_clientsession",
        return_value=_patched_session(ok=True),
    ):
        result = await hass.services.async_call(
            DOMAIN,
            SERVICE_RECORD,
            {ATTR_URL: "https://example.com"},
            blocking=True,
            return_response=True,
        )
    assert result["ok"] is True
    assert "file" in result


async def test_handle_record_with_all_params(hass: HomeAssistant):
    await _setup_integration(hass)
    with patch(
        "custom_components.dashsnap.services.async_get_clientsession",
        return_value=_patched_session(ok=True),
    ) as mock_sess:
        session = mock_sess.return_value
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RECORD,
            {
                ATTR_URL: "https://grafana.example.com/d/xyz",
                ATTR_TARGET: "grafana",
                ATTR_SECONDS: 10,
                ATTR_VIEWPORT_WIDTH: 1280,
                ATTR_VIEWPORT_HEIGHT: 720,
                ATTR_FORMAT: "png",
            },
            blocking=True,
            return_response=True,
        )
    called_url = session.post.call_args[0][0]
    assert "target=grafana" in called_url
    assert "seconds=10" in called_url
    assert "viewport_width=1280" in called_url
    assert "viewport_height=720" in called_url
    assert "format=png" in called_url


async def test_handle_record_delay_param(hass: HomeAssistant):
    await _setup_integration(hass)
    with patch(
        "custom_components.dashsnap.services.async_get_clientsession",
        return_value=_patched_session(ok=True),
    ) as mock_sess:
        session = mock_sess.return_value
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RECORD,
            {ATTR_URL: "https://example.com", ATTR_DELAY: 5},
            blocking=True,
            return_response=True,
        )
    called_url = session.post.call_args[0][0]
    assert "delay=5" in called_url


async def test_handle_record_no_target_param(hass: HomeAssistant):
    """When target not supplied, it should not appear in query string."""
    await _setup_integration(hass)
    with patch(
        "custom_components.dashsnap.services.async_get_clientsession",
        return_value=_patched_session(ok=True),
    ) as mock_sess:
        session = mock_sess.return_value
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RECORD,
            {ATTR_URL: "https://example.com"},
            blocking=True,
            return_response=True,
        )
    called_url = session.post.call_args[0][0]
    assert "target" not in called_url


async def test_handle_record_failure_raises(hass: HomeAssistant):
    await _setup_integration(hass)
    with patch(
        "custom_components.dashsnap.services.async_get_clientsession",
        return_value=_patched_session(ok=False),
    ):
        with pytest.raises(HomeAssistantError, match="Recording failed"):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RECORD,
                {ATTR_URL: "https://example.com"},
                blocking=True,
                return_response=True,
            )


async def test_handle_record_network_error_raises(hass: HomeAssistant):
    await _setup_integration(hass)
    session = MagicMock()
    session.post = MagicMock(side_effect=Exception("connection refused"))
    with patch("custom_components.dashsnap.services.async_get_clientsession", return_value=session):
        with pytest.raises(HomeAssistantError, match="Could not reach DashSnap"):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RECORD,
                {ATTR_URL: "https://example.com"},
                blocking=True,
                return_response=True,
            )


# ---------------------------------------------------------------------------
# handle_record_ha
# ---------------------------------------------------------------------------


async def test_handle_record_ha_success(hass: HomeAssistant):
    await _setup_integration(hass)
    with patch(
        "custom_components.dashsnap.services.async_get_clientsession",
        return_value=_patched_session(ok=True),
    ) as mock_sess:
        session = mock_sess.return_value
        result = await hass.services.async_call(
            DOMAIN,
            SERVICE_RECORD_HA,
            {ATTR_PATH: "/lovelace/0"},
            blocking=True,
            return_response=True,
        )
    assert result["ok"] is True
    called_url = session.post.call_args[0][0]
    assert "/record/ha" in called_url
    assert "path=%2Flovelace%2F0" in called_url


async def test_handle_record_ha_with_target(hass: HomeAssistant):
    await _setup_integration(hass)
    with patch(
        "custom_components.dashsnap.services.async_get_clientsession",
        return_value=_patched_session(ok=True),
    ) as mock_sess:
        session = mock_sess.return_value
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RECORD_HA,
            {ATTR_PATH: "/lovelace/0", ATTR_TARGET: "ha"},
            blocking=True,
            return_response=True,
        )
    called_url = session.post.call_args[0][0]
    assert "target=ha" in called_url


async def test_handle_record_ha_with_all_params(hass: HomeAssistant):
    await _setup_integration(hass)
    with patch(
        "custom_components.dashsnap.services.async_get_clientsession",
        return_value=_patched_session(ok=True),
    ) as mock_sess:
        session = mock_sess.return_value
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RECORD_HA,
            {
                ATTR_PATH: "/lovelace/0",
                ATTR_VIEWPORT_WIDTH: 1280,
                ATTR_VIEWPORT_HEIGHT: 720,
                ATTR_FORMAT: "png",
            },
            blocking=True,
            return_response=True,
        )
    called_url = session.post.call_args[0][0]
    assert "viewport_width=1280" in called_url
    assert "viewport_height=720" in called_url
    assert "format=png" in called_url


async def test_handle_record_ha_failure_raises(hass: HomeAssistant):
    await _setup_integration(hass)
    with patch(
        "custom_components.dashsnap.services.async_get_clientsession",
        return_value=_patched_session(ok=False),
    ):
        with pytest.raises(HomeAssistantError, match="Recording failed"):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RECORD_HA,
                {ATTR_PATH: "/lovelace/0"},
                blocking=True,
                return_response=True,
            )


async def test_handle_record_ha_network_error_raises(hass: HomeAssistant):
    await _setup_integration(hass)
    session = MagicMock()
    session.post = MagicMock(side_effect=Exception("timeout"))
    with patch("custom_components.dashsnap.services.async_get_clientsession", return_value=session):
        with pytest.raises(HomeAssistantError, match="Could not reach DashSnap"):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RECORD_HA,
                {ATTR_PATH: "/lovelace/0"},
                blocking=True,
                return_response=True,
            )
