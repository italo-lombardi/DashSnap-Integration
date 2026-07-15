"""Tests for DashSnap integration __init__.py."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dashsnap.const import CONF_BASE_URL, CONF_TARGETS, DOMAIN


async def test_async_setup_entry_stores_data(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    mock_config_entry.add_to_hass(hass)
    with patch("custom_components.dashsnap.async_register_services"):
        result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert result is True
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]
    stored = hass.data[DOMAIN][mock_config_entry.entry_id]
    assert stored["base_url"] == "http://dashsnap:8099"
    assert stored["targets"] == [{"name": "ha", "strategy": "ha_token"}]


async def test_async_setup_entry_options_override(hass: HomeAssistant):
    entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="DashSnap",
        data={CONF_BASE_URL: "http://dashsnap:8099", CONF_TARGETS: []},
        options={
            CONF_BASE_URL: "http://other:8099",
            CONF_TARGETS: [{"name": "x", "strategy": "none"}],
        },
        entry_id="opt_entry",
        unique_id=DOMAIN + "_opt",
    )
    entry.add_to_hass(hass)
    with patch("custom_components.dashsnap.async_register_services"):
        await hass.config_entries.async_setup(entry.entry_id)
    stored = hass.data[DOMAIN][entry.entry_id]
    assert stored["base_url"] == "http://other:8099"
    assert stored["targets"] == [{"name": "x", "strategy": "none"}]


async def test_async_setup_entry_data_fallback_when_no_options(hass: HomeAssistant):
    entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="DashSnap",
        data={CONF_BASE_URL: "http://dashsnap:8099"},
        entry_id="no_targets_entry",
        unique_id=DOMAIN + "_nf",
    )
    entry.add_to_hass(hass)
    with patch("custom_components.dashsnap.async_register_services"):
        await hass.config_entries.async_setup(entry.entry_id)
    stored = hass.data[DOMAIN][entry.entry_id]
    assert stored["targets"] == []


async def test_update_listener_updates_data(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    mock_config_entry.add_to_hass(hass)
    with patch("custom_components.dashsnap.async_register_services"):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)

    # Simulate options update
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={CONF_BASE_URL: "http://new:8099", CONF_TARGETS: []},
    )
    await hass.async_block_till_done()

    stored = hass.data[DOMAIN][mock_config_entry.entry_id]
    assert stored["base_url"] == "http://new:8099"


async def test_async_unload_entry_removes_data(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    mock_config_entry.add_to_hass(hass)
    with patch("custom_components.dashsnap.async_register_services"):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)

    with patch("custom_components.dashsnap.async_unregister_services") as mock_unreg:
        result = await hass.config_entries.async_unload(mock_config_entry.entry_id)

    assert result is True
    assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})
    mock_unreg.assert_called_once()


async def test_async_unload_entry_keeps_services_when_other_entry_loaded(hass: HomeAssistant):
    """When a second entry is still loaded, unregister is not called."""
    from custom_components.dashsnap import async_setup_entry, async_unload_entry

    entry1 = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="DashSnap1",
        data={CONF_BASE_URL: "http://a:8099", CONF_TARGETS: []},
        entry_id="e1",
        unique_id=DOMAIN + "_e1",
    )
    entry2 = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="DashSnap2",
        data={CONF_BASE_URL: "http://b:8099", CONF_TARGETS: []},
        entry_id="e2",
        unique_id=DOMAIN + "_e2",
    )

    with patch("custom_components.dashsnap.async_register_services"):
        await async_setup_entry(hass, entry1)
        await async_setup_entry(hass, entry2)

    with patch("custom_components.dashsnap.async_unregister_services") as mock_unreg:
        result = await async_unload_entry(hass, entry1)

    assert result is True
    # entry2 still in hass.data → unregister NOT called
    assert entry2.entry_id in hass.data[DOMAIN]
    mock_unreg.assert_not_called()
