"""DashSnap integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_BASE_URL, DOMAIN
from .services import async_register_services, async_unregister_services

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    base_url = entry.options.get(CONF_BASE_URL, entry.data[CONF_BASE_URL])
    hass.data[DOMAIN][entry.entry_id] = {"base_url": base_url}
    _LOGGER.warning(
        "DashSnap addon URL: %s — change in Settings → Devices & Services → DashSnap → Configure if wrong",
        base_url,
    )
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async_register_services(hass)  # guard inside services.py prevents double-registration
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    base_url = entry.options.get(CONF_BASE_URL, entry.data[CONF_BASE_URL])
    hass.data[DOMAIN][entry.entry_id] = {"base_url": base_url}


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data[DOMAIN].pop(entry.entry_id, None)
    if not hass.data[DOMAIN]:
        async_unregister_services(hass)
    return True
