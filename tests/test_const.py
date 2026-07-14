"""Tests for const.py — just imports; ensures no syntax errors and all symbols exist."""

from custom_components.dashsnap.const import (
    ATTR_FORMAT,
    ATTR_PATH,
    ATTR_SECONDS,
    ATTR_TARGET,
    ATTR_URL,
    ATTR_VIEWPORT_HEIGHT,
    ATTR_VIEWPORT_WIDTH,
    CONF_BASE_URL,
    CONF_TARGETS,
    DEFAULT_BASE_URL,
    DEFAULT_FORMAT,
    DEFAULT_SECONDS,
    DEFAULT_VIEWPORT_HEIGHT,
    DEFAULT_VIEWPORT_WIDTH,
    DOMAIN,
    HEALTH_TIMEOUT,
    RECORD_TIMEOUT,
    SERVICE_RECORD,
    SERVICE_RECORD_HA,
)


def test_constants():
    assert DOMAIN == "dashsnap"
    assert CONF_BASE_URL == "base_url"
    assert CONF_TARGETS == "targets"
    assert SERVICE_RECORD == "record"
    assert SERVICE_RECORD_HA == "record_ha"
    assert ATTR_URL == "url"
    assert ATTR_PATH == "path"
    assert ATTR_TARGET == "target"
    assert ATTR_SECONDS == "seconds"
    assert ATTR_VIEWPORT_WIDTH == "viewport_width"
    assert ATTR_VIEWPORT_HEIGHT == "viewport_height"
    assert ATTR_FORMAT == "format"
    assert DEFAULT_SECONDS == 30
    assert DEFAULT_VIEWPORT_WIDTH == 1920
    assert DEFAULT_VIEWPORT_HEIGHT == 1080
    assert DEFAULT_FORMAT == "webm"
    assert HEALTH_TIMEOUT == 10
    assert RECORD_TIMEOUT == 900
    assert DEFAULT_BASE_URL == "http://homeassistant.local:8099"
