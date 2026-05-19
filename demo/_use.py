"""Demo: import the freshly generated SDK and make a typed call.

Offline + deterministic (httpx MockTransport) so the demo always works on
camera — no API key, no network. Swap the transport for a real key to hit
https://api.pugetsound.onebusaway.org for real.
"""

import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent / "out"))

from onebusaway import OnebusawaySDK  # noqa: E402  (generated)

_RESP = {
    "code": 200, "currentTime": 1_700_000_000, "text": "OK", "version": 2,
    "data": {
        "entry": {"id": "1", "name": "Metro Transit",
                  "timezone": "America/Los_Angeles",
                  "url": "https://metrotransit.example"},
        "references": {"agencies": [], "routes": [], "situations": [],
                       "stopTimes": [], "stops": [], "trips": []},
    },
}

client = OnebusawaySDK(
    api_key="demo-key",
    http_client=httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=_RESP))
    ),
)

agency = client.agency.retrieve("1")
print(f"  client.agency.retrieve('1') -> {type(agency).__name__}")
print(f"  agency.data.entry.name      = {agency.data.entry.name!r}")
print(f"  fully typed (pydantic)      : {type(agency.data.entry).__name__}")
