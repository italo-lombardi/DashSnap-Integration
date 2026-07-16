"""Config flow for DashSnap integration."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .const import CONF_BASE_URL, DEFAULT_BASE_URL, DOMAIN, HEALTH_TIMEOUT

_PROBE_URLS = [
    "http://dashsnap:8099",
    "http://host.docker.internal:8099",
]

PROBE_TIMEOUT = 3


async def _health(
    hass: HomeAssistant, base_url: str, timeout: int = HEALTH_TIMEOUT
) -> tuple[bool, str, str]:
    if not base_url.startswith(("http://", "https://")):
        return False, "invalid_url", base_url
    session = async_get_clientsession(hass)
    try:
        async with session.get(f"{base_url.rstrip('/')}/health", timeout=timeout) as resp:
            data = await resp.json(content_type=None)
    except Exception:  # noqa: BLE001
        return False, "cannot_connect", base_url
    if data.get("ok"):
        self_urls = [
            u
            for u in data.get("self_urls", [])
            if urlparse(u).hostname not in ("localhost", "127.0.0.1", "::1")
        ]
        canonical = self_urls[0].rstrip("/") if self_urls else base_url.rstrip("/")
        return True, "", canonical
    return False, "app_unhealthy", base_url


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
            ok, reason, canonical = await _health(self.hass, base_url)
            if ok:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="DashSnap",
                    data={CONF_BASE_URL: canonical},
                )
            errors["base"] = reason
            default = base_url
        else:
            detected = await self._autodetect()
            if detected is not None:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="DashSnap",
                    data={CONF_BASE_URL: detected},
                )
            default = DEFAULT_BASE_URL

        schema = vol.Schema({vol.Required(CONF_BASE_URL, default=default): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def _autodetect(self) -> str | None:
        token = os.environ.get("SUPERVISOR_TOKEN")
        if token:
            url = await self._supervisor_addon_url(token)
            if url:
                ok, _, canonical = await _health(self.hass, url)
                if ok:
                    return canonical
        for candidate in _PROBE_URLS:
            ok, _, canonical = await _health(self.hass, candidate, PROBE_TIMEOUT)
            if ok:
                return canonical
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
                host = addon.get("hostname") or slug.replace("_", "-")
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
            ok, reason, canonical = await _health(self.hass, base_url)
            if ok:
                return self.async_create_entry(data={CONF_BASE_URL: canonical})
            errors["base"] = reason
            current = base_url
        schema = vol.Schema({vol.Required(CONF_BASE_URL, default=current): str})
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
