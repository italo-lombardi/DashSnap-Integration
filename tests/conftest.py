"""Shared fixtures for DashSnap integration tests."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dashsnap.const import CONF_BASE_URL, CONF_TARGETS, DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_config_entry():
    return MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="DashSnap",
        data={
            CONF_BASE_URL: "http://dashsnap:8099",
            CONF_TARGETS: [{"name": "ha", "strategy": "ha_token"}],
        },
        entry_id="test_entry_id",
        unique_id=DOMAIN,
    )
