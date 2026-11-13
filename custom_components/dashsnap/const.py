"""Constants for the DashSnap integration."""

DOMAIN = "dashsnap"

CONF_BASE_URL = "base_url"

DEFAULT_BASE_URL = "http://homeassistant.local:8099"

SERVICE_RECORD = "record"
SERVICE_RECORD_HA = "record_ha"
SERVICE_LIST_RECORDINGS = "list_recordings"
SERVICE_DELETE_RECORDINGS = "delete_recordings"

ATTR_URL = "url"
ATTR_PATH = "path"
ATTR_TARGET = "target"
ATTR_SECONDS = "seconds"
ATTR_DELAY = "delay"
ATTR_VIEWPORT_WIDTH = "viewport_width"
ATTR_VIEWPORT_HEIGHT = "viewport_height"
ATTR_FORMAT = "format"
ATTR_LANG = "lang"

# Delete/list filters
ATTR_NAME = "name"
ATTR_SLUG = "slug"
ATTR_OLDER_THAN_DAYS = "older_than_days"
ATTR_DELETE_ALL = "delete_all"
ATTR_DRY_RUN = "dry_run"

# Validation at the HA trust boundary (mirror of the addon sanitizer, record.py).
# Slug: exact output of the addon's _safe_filename_component -> [a-zA-Z0-9_]{1,40}.
SLUG_RE = r"^[A-Za-z0-9_]{1,40}$"
# Recording filename: {YYYYMMDD_HHMMSS}_{slug}.{ext}
RECORDING_NAME_RE = r"^\d{8}_\d{6}_[A-Za-z0-9_]{1,40}\.(?:webm|png)$"

DEFAULT_SECONDS = 30
DEFAULT_FORMAT = "webm"

HEALTH_TIMEOUT = 10
RECORD_TIMEOUT = 900
# Listing/deleting is a cheap directory op on the addon; don't tie it up for 15 min.
RECORDINGS_TIMEOUT = 30
# Connect-phase cap: a dead/wedged renderer that still has a socket in LISTEN
# accepts the TCP connection but never answers. Without this, a hung app blocks
# the caller for the full RECORD_TIMEOUT (15 min). Fail the connect in 10s so it
# surfaces as a ClientError -> rediscover, while the long total still allows a
# legitimately long capture once connected. 10s (not 5s) gives margin for a
# heavily-loaded host to accept() the connection.
SOCK_CONNECT_TIMEOUT = 10
