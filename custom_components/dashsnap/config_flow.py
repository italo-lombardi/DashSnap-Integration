"""Config flow for DashSnap integration."""

from __future__ import annotations

import os
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_BASE_URL, CONF_TARGETS, DEFAULT_BASE_URL, DOMAIN, HEALTH_TIMEOUT

_PROBE_URLS = [
    "http://dashsnap:8099",
    "http://host.docker.internal:8099",
    "http://localhost:8099",
    "http://homeassistant.local:8099",
]

PROBE_TIMEOUT = 3


async def _health(
    hass: HomeAssistant, base_url: str, timeout: int = HEALTH_TIMEOUT
) -> tuple[bool, str]:
    if not base_url.startswith(("http://", "https://")):
        return False, "invalid_url"
    session = async_get_clientsession(hass)
    try:
        async with session.get(f"{base_url.rstrip('/')}/health", timeout=timeout) as resp:
            data = await resp.json(content_type=None)
    except Exception:  # noqa: BLE001
        return False, "cannot_connect"
    if data.get("ok"):
        return True, ""
    return False, "app_unhealthy"


async def _fetch_targets(hass: HomeAssistant, base_url: str) -> list[dict]:
    session = async_get_clientsession(hass)
    try:
        async with session.get(f"{base_url.rstrip('/')}/targets", timeout=HEALTH_TIMEOUT) as r:
            data = await r.json(content_type=None)
            return data.get("targets", [])
    except Exception:  # noqa: BLE001
        return []


class DashSnapConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return DashSnapOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            ok, reason = await _health(self.hass, base_url)
            if ok:
                targets = await _fetch_targets(self.hass, base_url)
                return self.async_create_entry(
                    title="DashSnap",
                    data={CONF_BASE_URL: base_url, CONF_TARGETS: targets},
                )
            errors["base"] = reason
            default = base_url
        else:
            detected = await self._autodetect()
            if detected is not None:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                targets = await _fetch_targets(self.hass, detected)
                return self.async_create_entry(
                    title="DashSnap",
                    data={CONF_BASE_URL: detected, CONF_TARGETS: targets},
                )
            default = DEFAULT_BASE_URL

        schema = vol.Schema({vol.Required(CONF_BASE_URL, default=default): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def _autodetect(self) -> str | None:
        token = os.environ.get("SUPERVISOR_TOKEN")
        if token:
            url = await self._supervisor_addon_url(token)
            if url and (await _health(self.hass, url))[0]:
                return url
        for candidate in _PROBE_URLS:
            if (await _health(self.hass, candidate, PROBE_TIMEOUT))[0]:
                return candidate
        return None

    async def _supervisor_addon_url(self, token: str) -> str | None:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                "http://supervisor/addons",
                headers={"Authorization": f"Bearer {token}"},
                timeout=HEALTH_TIMEOUT,
            ) as resp:
                data = await resp.json(content_type=None)
        except Exception:  # noqa: BLE001
            return None
        for addon in data.get("data", {}).get("addons", []):
            slug = addon.get("slug", "")
            if "dashsnap" in slug:
                host = addon.get("hostname") or slug.replace("-", "_")
                return f"http://{host}:8099"
        return None


class DashSnapOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        current = self.config_entry.options.get(
            CONF_BASE_URL, self.config_entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)
        )
        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            ok, reason = await _health(self.hass, base_url)
            if ok:
                targets = await _fetch_targets(self.hass, base_url)
                return self.async_create_entry(
                    data={CONF_BASE_URL: base_url, CONF_TARGETS: targets}
                )
            errors["base"] = reason
            current = base_url
        schema = vol.Schema({vol.Required(CONF_BASE_URL, default=current): str})
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
