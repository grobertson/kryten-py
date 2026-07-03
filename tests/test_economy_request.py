"""Tests for economy_request method (Gap 8)."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from kryten.client import KrytenClient
from kryten.exceptions import KrytenConnectionError
from kryten.mock import MockKrytenClient

_CONFIG = {
    "nats": {"servers": ["nats://localhost:4222"]},
    "channels": [{"domain": "cytu.be", "channel": "Q_A"}],
    "service": {"name": "test-service"},
}


def _make_client(response_data: dict) -> KrytenClient:
    client = KrytenClient(_CONFIG)
    client._connected = True
    mock_nats = AsyncMock()
    msg = MagicMock()
    msg.data = json.dumps(response_data).encode()
    mock_nats.request = AsyncMock(return_value=msg)
    client._nats = mock_nats
    return client


async def test_economy_request_envelope():
    """Payload must be flat — command and channel at top level alongside extra fields."""
    expected_response = {"success": True, "data": {"balance": 2000}}
    client = _make_client(expected_response)

    result = await client.economy_request("Q_A", "balance.get", {"username": "alice"})

    client._nats.request.assert_called_once()
    subject, raw_payload, *_ = client._nats.request.call_args[0]
    assert subject == "kryten.economy.command"
    sent = json.loads(raw_payload.decode())
    assert sent["command"] == "balance.get"
    assert sent["channel"] == "Q_A"
    assert sent["username"] == "alice"
    # Ensure payload is NOT nested
    assert "payload" not in sent
    assert result == expected_response


async def test_economy_request_timeout_forwarded():
    """Custom timeout is forwarded to nats_request."""
    client = _make_client({"success": True, "data": {}})

    await client.economy_request("Q_A", "balance.get", {}, timeout=2.5)

    call_kwargs = client._nats.request.call_args[1]
    assert call_kwargs.get("timeout") == 2.5


async def test_economy_request_not_connected():
    """Raises KrytenConnectionError when not connected."""
    client = KrytenClient(_CONFIG)
    # Deliberately not connected

    with pytest.raises(KrytenConnectionError):
        await client.economy_request("Q_A", "balance.get", {"username": "alice"})


# Mock tests

def _make_mock() -> MockKrytenClient:
    return MockKrytenClient(_CONFIG)


async def test_mock_economy_request_default():
    """Returns default response for unknown commands."""
    async with _make_mock() as mock:
        result = await mock.economy_request("Q_A", "unknown.command", {})
    assert result == {"success": True, "data": {}}


async def test_mock_economy_request_preset():
    """Returns preset response when _economy_responses[command] is set."""
    async with _make_mock() as mock:
        mock._economy_responses["balance.get"] = {
            "success": True,
            "data": {"found": True, "balance": 500},
        }
        result = await mock.economy_request("Q_A", "balance.get", {"username": "bob"})
    assert result["success"] is True
    assert result["data"]["balance"] == 500
