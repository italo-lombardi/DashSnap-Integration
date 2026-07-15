"""Constants for the DashSnap integration."""

DOMAIN = "dashsnap"

CONF_BASE_URL = "base_url"

DEFAULT_BASE_URL = "http://homeassistant.local:8099"

SERVICE_RECORD = "record"
SERVICE_RECORD_HA = "record_ha"

ATTR_URL = "url"
ATTR_PATH = "path"
ATTR_TARGET = "target"
ATTR_SECONDS = "seconds"
ATTR_VIEWPORT_WIDTH = "viewport_width"
ATTR_VIEWPORT_HEIGHT = "viewport_height"
ATTR_FORMAT = "format"

DEFAULT_SECONDS = 30
DEFAULT_VIEWPORT_WIDTH = 1920
DEFAULT_VIEWPORT_HEIGHT = 1080
DEFAULT_FORMAT = "webm"

HEALTH_TIMEOUT = 10
RECORD_TIMEOUT = 900
