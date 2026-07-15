"""Services for DashSnap: forward to the DashSnap HTTP API."""

from __future__ import annotations

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
    DEFAULT_VIEWPORT_HEIGHT,
    DEFAULT_VIEWPORT_WIDTH,
    DOMAIN,
    RECORD_TIMEOUT,
    SERVICE_RECORD,
    SERVICE_RECORD_HA,
)

_COMMON = {
    vol.Optional(ATTR_SECONDS, default=DEFAULT_SECONDS): vol.All(int, vol.Range(min=1, max=600)),
    vol.Optional(ATTR_DELAY, default=0): vol.All(int, vol.Range(min=0, max=60)),
    vol.Optional(ATTR_VIEWPORT_WIDTH, default=DEFAULT_VIEWPORT_WIDTH): vol.All(
        int, vol.Range(min=320, max=3840)
    ),
    vol.Optional(ATTR_VIEWPORT_HEIGHT, default=DEFAULT_VIEWPORT_HEIGHT): vol.All(
        int, vol.Range(min=240, max=2160)
    ),
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


async def _call_app(hass: HomeAssistant, endpoint: str, params: dict) -> dict:
    session = async_get_clientsession(hass)
    url = f"{_base_url(hass)}{endpoint}?{urlencode(params)}"
    try:
        async with session.post(url, timeout=aiohttp.ClientTimeout(total=RECORD_TIMEOUT)) as resp:
            data = await resp.json(content_type=None)
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
            "viewport_width": call.data[ATTR_VIEWPORT_WIDTH],
            "viewport_height": call.data[ATTR_VIEWPORT_HEIGHT],
            "format": call.data[ATTR_FORMAT],
        }
        if ATTR_TARGET in call.data:
            params["target"] = call.data[ATTR_TARGET]
        return await _call_app(hass, "/record", params)

    async def handle_record_ha(call: ServiceCall) -> dict:
        params = {
            "path": call.data[ATTR_PATH],
            "seconds": call.data[ATTR_SECONDS],
            "delay": call.data[ATTR_DELAY],
            "viewport_width": call.data[ATTR_VIEWPORT_WIDTH],
            "viewport_height": call.data[ATTR_VIEWPORT_HEIGHT],
            "format": call.data[ATTR_FORMAT],
        }
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
