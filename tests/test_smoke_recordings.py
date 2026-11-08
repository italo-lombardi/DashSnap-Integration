"""Live smoke test for the recordings list/delete HTTP glue.

Unlike test_services.py (which mocks the HTTP layer away), this drives the REAL
integration HTTP path — custom_components.dashsnap.services._request_recordings:
URL building (/recordings vs /recordings/delete), GET/POST method selection,
query encoding, and JSON response parsing — against a running DashSnap addon
container. It proves the integration's wire glue and the endpoint contract end
to end.

It deliberately does NOT use the Home Assistant `hass` fixture: that fixture's
autouse cleanup verifier forbids the lingering daemon thread aiohttp spawns when
a real connector is closed. The service-registration layer on top of this glue
(schema validation, error-slug -> HomeAssistantError mapping, boolean omit) is
fully covered by the mocked unit suite in test_services.py at 100%. Here we own
the aiohttp session and close it in a finally, so no thread lingers.

Run it explicitly against a running container (default http://127.0.0.1:8099):

    pytest -m smoke --no-cov

It is deselected from the default suite (addopts -m 'not smoke'). It FAILS
(never skips) when the container is unreachable, preserving the 0-skip bar.

SAFETY: every mutation is scoped to the exact unique filename this test records
(returned by /record, unique to the second). It NEVER uses slug=,
older_than_days=, or all= — so it cannot touch any pre-existing recording. A
finally block best-effort-deletes the clip it created.
"""

from __future__ import annotations

import os

import aiohttp
import pytest

from custom_components.dashsnap import services
from custom_components.dashsnap.const import RECORD_TIMEOUT

# 127.0.0.1, not localhost: pytest-socket (pulled in by the HA test plugin)
# allows 127.0.0.1 and blocks ::1, which "localhost" may resolve to first.
SMOKE_URL = os.environ.get("DASHSNAP_SMOKE_URL", "http://127.0.0.1:8099").rstrip("/")
SMOKE_TARGET = os.environ.get("DASHSNAP_SMOKE_TARGET", "public")
SMOKE_RECORD_URL = os.environ.get(
    "DASHSNAP_SMOKE_RECORD_URL", "http://www.infoshare.it/hp/?n=dashsnap-smoke"
)

pytestmark = pytest.mark.smoke


@pytest.fixture(autouse=True)
def _allow_sockets():
    """Enable real sockets when pytest-socket is active, no-op otherwise.

    The HA test plugin pulls in pytest-socket, which disables sockets globally;
    this smoke needs real network I/O. But a bare CI env may not have the plugin
    (then there is nothing to re-enable), so don't hard-require the socket_enabled
    fixture — enable conditionally.
    """
    try:
        import pytest_socket

        pytest_socket.enable_socket()
    except Exception:  # noqa: BLE001
        pass
    yield


@pytest.fixture(autouse=True)
def verify_cleanup():
    """Override the HA plugin's strict cleanup verifier for this module.

    The plugin's autouse verify_cleanup asserts no non-dummy threads survive a
    test. A real aiohttp.ClientSession closing under asyncio debug mode spawns a
    short-lived `_run_safe_shutdown_loop` daemon thread that outlives the test
    body — harmless, but it trips that assert. This smoke deliberately does real
    aiohttp I/O (that is what it exists to prove), so we no-op the verifier here.
    The mocked unit suite keeps the strict verifier.
    """
    yield


async def _record(session: aiohttp.ClientSession) -> dict:
    """POST /record directly (not an integration helper — just to create a clip)."""
    from urllib.parse import urlencode

    params = {
        "url": SMOKE_RECORD_URL,
        "seconds": 1,
        "delay": 0,
        "format": "png",
        "target": SMOKE_TARGET,
    }
    url = f"{SMOKE_URL}/record?{urlencode(params)}"
    async with session.post(url, timeout=aiohttp.ClientTimeout(total=RECORD_TIMEOUT)) as resp:
        return await resp.json(content_type=None)


async def test_live_recordings_glue(monkeypatch):
    """record -> list -> dry_run delete -> delete -> gone via the real HTTP glue."""
    session = aiohttp.ClientSession()
    # _request_recordings calls async_get_clientsession(hass); hand it our session
    # (hass is unused by that helper beyond this call), so we own the lifecycle.
    monkeypatch.setattr(services, "async_get_clientsession", lambda _hass: session)

    async def list_names() -> list[str]:
        data = await services._request_recordings(None, "get", SMOKE_URL, {})
        assert data.get("ok") is True, f"list not ok: {data}"
        return [r["name"] for r in data["recordings"]]

    name = None
    try:
        # 1. Create a uniquely-named clip. Fail loudly (not skip) if the container is down.
        try:
            rec = await _record(session)
        except Exception as err:  # noqa: BLE001
            pytest.fail(
                f"Could not reach DashSnap at {SMOKE_URL}: {err}. "
                "Start the container (docker compose up -d) and retry."
            )
        assert rec.get("ok") is True, f"record did not return ok: {rec}"
        name = os.path.basename(rec["file"])

        # 2. list includes it (real GET /recordings through the integration helper).
        assert name in await list_names(), f"{name} not listed after record"

        # 3. dry-run delete by exact name: reports it, removes nothing.
        dry = await services._request_recordings(
            None, "post", SMOKE_URL, {"name": name, "dry_run": "true"}
        )
        assert dry["ok"] is True and dry["deleted"] == [name]
        assert dry["count"] == 1 and dry["dry_run"] is True
        assert name in await list_names(), "dry_run must not remove the file"

        # 4. real delete by exact name.
        res = await services._request_recordings(None, "post", SMOKE_URL, {"name": name})
        assert res["ok"] is True and res["deleted"] == [name]
        assert res["count"] == 1 and res["dry_run"] is False

        # 5. gone.
        assert name not in await list_names(), f"{name} still present after delete"
        name = None  # deleted; nothing to clean up

        # 6. error contract: filterless delete -> refuse_wipe (addon 400 body).
        rw = await services._request_recordings(None, "post", SMOKE_URL, {})
        assert rw["ok"] is False and rw["error"] == "refuse_wipe"

        # 7. not_found for a well-formed-but-absent name.
        nf = await services._request_recordings(
            None, "post", SMOKE_URL, {"name": "20260101_000000_nope.png"}
        )
        assert nf["ok"] is False and nf["error"] == "not_found"

        # 8. invalid_name for a malformed name.
        inv = await services._request_recordings(None, "post", SMOKE_URL, {"name": "badname.txt"})
        assert inv["ok"] is False and inv["error"] == "invalid_name"
    finally:
        if name is not None:
            try:
                await services._request_recordings(None, "post", SMOKE_URL, {"name": name})
            except Exception:  # noqa: BLE001, S110
                pass
        await session.close()
