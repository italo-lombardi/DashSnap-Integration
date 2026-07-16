"""Services for DashSnap: forward to the DashSnap HTTP API."""

from __future__ import annotations

import logging
from urllib.parse import urlencode

import aiohttp
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .const import (
    ATTR_DELAY,
    ATTR_FORMAT,
    ATTR_PATH,
    ATTR_SECONDS,
    ATTR_TARGET,
    ATTR_URL,
    ATTR_VIEWPORT_HEIGHT,
    ATTR_VIEWPORT_WIDTH,
    DEFAULT_FORMAT,
    DEFAULT_SECONDS,
    DOMAIN,
    RECORD_TIMEOUT,
    SERVICE_RECORD,
    SERVICE_RECORD_HA,
)

_LOGGER = logging.getLogger(__name__)

_COMMON = {
    vol.Optional(ATTR_SECONDS, default=DEFAULT_SECONDS): vol.All(
        vol.Coerce(int), vol.Range(min=1, max=600)
    ),
    vol.Optional(ATTR_DELAY, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
    vol.Optional(ATTR_VIEWPORT_WIDTH): vol.All(vol.Coerce(int), vol.Range(min=320, max=3840)),
    vol.Optional(ATTR_VIEWPORT_HEIGHT): vol.All(vol.Coerce(int), vol.Range(min=240, max=2160)),
    vol.Optional(ATTR_FORMAT, default=DEFAULT_FORMAT): vol.In(["webm", "png"]),
    vol.Optional(ATTR_TARGET): cv.string,
}

RECORD_SCHEMA = vol.Schema({vol.Required(ATTR_URL): cv.string, **_COMMON})
RECORD_HA_SCHEMA = vol.Schema({vol.Required(ATTR_PATH): cv.string, **_COMMON})


def _base_url(hass: HomeAssistant) -> str:
    entry_data = next(iter(hass.data.get(DOMAIN, {}).values()), None)
    if not entry_data:
        raise HomeAssistantError("DashSnap is not configured")
    return entry_data["base_url"].rstrip("/")


async def _rediscover(hass: HomeAssistant) -> str | None:
    """Re-probe for the addon URL and update stored config if found."""
    import os  # noqa: PLC0415

    from .config_flow import (  # noqa: PLC0415
        _PROBE_URLS,
        PROBE_TIMEOUT,
        _health,
        _supervisor_addon_url,
    )

    entry = next(iter(hass.config_entries.async_entries(DOMAIN)), None)
    if entry is None:
        return None

    if hass.data[DOMAIN].get("_rediscovering"):
        return None
    hass.data[DOMAIN]["_rediscovering"] = True
    try:
        candidates = list(_PROBE_URLS)
        supervisor_token = os.environ.get("SUPERVISOR_TOKEN")
        if supervisor_token:
            sup_url = await _supervisor_addon_url(hass, supervisor_token)
            if sup_url:
                candidates.insert(0, sup_url)

        for candidate in candidates:
            ok, _, canonical = await _health(hass, candidate, PROBE_TIMEOUT)
            if ok:
                hass.config_entries.async_update_entry(
                    entry, data={**entry.data, "base_url": canonical}
                )
                hass.data[DOMAIN][entry.entry_id] = {"base_url": canonical}
                _LOGGER.warning("DashSnap URL updated to %s after connection failure", canonical)
                return canonical
    finally:
        hass.data[DOMAIN].pop("_rediscovering", None)
    return None


async def _call_app(hass: HomeAssistant, endpoint: str, params: dict) -> dict:
    session = async_get_clientsession(hass)
    url = f"{_base_url(hass)}{endpoint}?{urlencode(params)}"
    try:
        async with session.post(url, timeout=aiohttp.ClientTimeout(total=RECORD_TIMEOUT)) as resp:
            data = await resp.json(content_type=None)
    except (aiohttp.ClientConnectionError, aiohttp.ServerDisconnectedError) as err:
        new_url = await _rediscover(hass)
        if new_url is None:
            raise HomeAssistantError(f"Could not reach DashSnap: {err}") from err
        url = f"{new_url}{endpoint}?{urlencode(params)}"
        try:
            async with session.post(
                url, timeout=aiohttp.ClientTimeout(total=RECORD_TIMEOUT)
            ) as resp:
                data = await resp.json(content_type=None)
        except Exception as retry_err:  # noqa: BLE001
            raise HomeAssistantError(f"Could not reach DashSnap: {retry_err}") from retry_err
    except Exception as err:  # noqa: BLE001
        raise HomeAssistantError(f"Could not reach DashSnap: {err}") from err
    if not data.get("ok", False):
        raise HomeAssistantError(f"Recording failed: {data.get('error', data)}")
    return data


def async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_RECORD) and hass.services.has_service(
        DOMAIN, SERVICE_RECORD_HA
    ):
        return

    async def handle_record(call: ServiceCall) -> dict:
        params = {
            "url": call.data[ATTR_URL],
            "seconds": call.data[ATTR_SECONDS],
            "delay": call.data[ATTR_DELAY],
            "format": call.data[ATTR_FORMAT],
        }
        if ATTR_VIEWPORT_WIDTH in call.data:
            params["viewport_width"] = call.data[ATTR_VIEWPORT_WIDTH]
        if ATTR_VIEWPORT_HEIGHT in call.data:
            params["viewport_height"] = call.data[ATTR_VIEWPORT_HEIGHT]
        if ATTR_TARGET in call.data:
            params["target"] = call.data[ATTR_TARGET]
        return await _call_app(hass, "/record", params)

    async def handle_record_ha(call: ServiceCall) -> dict:
        params = {
            "path": call.data[ATTR_PATH],
            "seconds": call.data[ATTR_SECONDS],
            "delay": call.data[ATTR_DELAY],
            "format": call.data[ATTR_FORMAT],
        }
        if ATTR_VIEWPORT_WIDTH in call.data:
            params["viewport_width"] = call.data[ATTR_VIEWPORT_WIDTH]
        if ATTR_VIEWPORT_HEIGHT in call.data:
            params["viewport_height"] = call.data[ATTR_VIEWPORT_HEIGHT]
        if ATTR_TARGET in call.data:
            params["target"] = call.data[ATTR_TARGET]
        return await _call_app(hass, "/record/ha", params)

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD,
        handle_record,
        schema=RECORD_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD_HA,
        handle_record_ha,
        schema=RECORD_HA_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )


def async_unregister_services(hass: HomeAssistant) -> None:
    hass.services.async_remove(DOMAIN, SERVICE_RECORD)
    hass.services.async_remove(DOMAIN, SERVICE_RECORD_HA)
