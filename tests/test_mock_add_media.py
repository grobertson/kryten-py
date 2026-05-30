"""Tests for mock add_media returning dict with uid (Gap 3)."""

from kryten.mock import MockKrytenClient


_CONFIG = {
    "nats": {"servers": ["nats://localhost:4222"]},
    "channels": [{"domain": "cytu.be", "channel": "lounge"}],
}


def _make_mock() -> MockKrytenClient:
    return MockKrytenClient(_CONFIG)


async def test_mock_add_media_returns_dict():
    """add_media must return a dict (not a correlation-ID string)."""
    async with _make_mock() as mock:
        result = await mock.add_media("lounge", "yt", "dQw4w9WgXcQ")
    assert isinstance(result, dict)
    assert "success" in result
    assert "uid" in result


async def test_mock_add_media_success_true():
    async with _make_mock() as mock:
        result = await mock.add_media("lounge", "yt", "dQw4w9WgXcQ")
    assert result["success"] is True


async def test_mock_add_media_uid_is_int():
    async with _make_mock() as mock:
        result = await mock.add_media("lounge", "yt", "dQw4w9WgXcQ")
    assert isinstance(result["uid"], int)


async def test_mock_add_media_records_command():
    """The call must still be recorded for test introspection."""
    async with _make_mock() as mock:
        await mock.add_media("lounge", "yt", "dQw4w9WgXcQ")
        commands = mock.get_published_commands()
    assert len(commands) == 1
    assert commands[0]["action"] == "queue"


async def test_mock_add_media_temp_param():
    """temp param must be recorded in the command body."""
    async with _make_mock() as mock:
        await mock.add_media("lounge", "yt", "abc", temp=False)
        commands = mock.get_published_commands()
    assert commands[0]["data"]["temp"] is False
