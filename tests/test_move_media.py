"""Tests for move_media int|str position (Gap 7)."""

import json
from unittest.mock import AsyncMock

from kryten.client import KrytenClient

_CONFIG = {
    "nats": {"servers": ["nats://localhost:4222"]},
    "channels": [{"domain": "cytu.be", "channel": "lounge"}],
    "service": {"name": "test-service"},
}


def _make_client() -> KrytenClient:
    client = KrytenClient(_CONFIG)
    client._connected = True
    client._nats = AsyncMock()
    return client


async def test_move_media_int_position():
    client = _make_client()
    await client.move_media("lounge", uid=10, position=42)

    client._nats.publish.assert_called_once()
    payload = json.loads(client._nats.publish.call_args[0][1].decode())
    assert payload["args"]["from"] == 10
    assert payload["args"]["after"] == 42


async def test_move_media_string_prepend():
    client = _make_client()
    await client.move_media("lounge", uid=10, position="prepend")

    payload = json.loads(client._nats.publish.call_args[0][1].decode())
    assert payload["args"]["after"] == "prepend"


async def test_move_media_string_append():
    client = _make_client()
    await client.move_media("lounge", uid=10, position="append")

    payload = json.loads(client._nats.publish.call_args[0][1].decode())
    assert payload["args"]["after"] == "append"
