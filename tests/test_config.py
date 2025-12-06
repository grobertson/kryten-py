"""Tests for configuration models."""

import json
import tempfile
from pathlib import Path

import pytest

from kryten.config import ChannelConfig, KrytenConfig, NatsConfig
from kryten.exceptions import KrytenValidationError


def test_nats_config_valid():
    """Test valid NATS configuration."""
    config = NatsConfig(servers=["nats://localhost:4222"])
    assert config.servers == ["nats://localhost:4222"]
    assert config.connect_timeout == 10
    assert config.max_reconnect_attempts == -1


def test_nats_config_requires_servers():
    """Test that servers list cannot be empty."""
    with pytest.raises(ValueError):
        NatsConfig(servers=[])


def test_channel_config_valid():
    """Test valid channel configuration."""
    config = ChannelConfig(domain="cytu.be", channel="lounge")
    assert config.domain == "cytu.be"
    assert config.channel == "lounge"


def test_channel_config_strips_whitespace():
    """Test that whitespace is stripped from domain and channel."""
    config = ChannelConfig(domain="  cytu.be  ", channel="  lounge  ")
    assert config.domain == "cytu.be"
    assert config.channel == "lounge"


def test_channel_config_rejects_empty():
    """Test that empty domain/channel is rejected."""
    with pytest.raises(ValueError):
        ChannelConfig(domain="", channel="lounge")

    with pytest.raises(ValueError):
        ChannelConfig(domain="cytu.be", channel="")


def test_kryten_config_valid():
    """Test valid complete configuration."""
    config = KrytenConfig(
        nats=NatsConfig(servers=["nats://localhost:4222"]),
        channels=[ChannelConfig(domain="cytu.be", channel="lounge")],
    )
    assert len(config.channels) == 1
    assert config.retry_attempts == 3
    assert config.handler_timeout == 30.0


def test_kryten_config_requires_channels():
    """Test that at least one channel is required."""
    with pytest.raises(ValueError):
        KrytenConfig(
            nats=NatsConfig(servers=["nats://localhost:4222"]),
            channels=[],
        )


def test_kryten_config_from_dict():
    """Test loading from dictionary."""
    config_dict = {
        "nats": {"servers": ["nats://localhost:4222"]},
        "channels": [{"domain": "cytu.be", "channel": "lounge"}],
    }
    config = KrytenConfig(**config_dict)
    assert len(config.channels) == 1


def test_kryten_config_from_json():
    """Test loading from JSON file."""
    config_data = {
        "nats": {"servers": ["nats://localhost:4222"]},
        "channels": [{"domain": "cytu.be", "channel": "lounge"}],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        config = KrytenConfig.from_json(temp_path)
        assert len(config.channels) == 1
        assert config.channels[0].domain == "cytu.be"
    finally:
        Path(temp_path).unlink()


def test_kryten_config_from_json_env_var_substitution(monkeypatch):
    """Test environment variable substitution in JSON."""
    monkeypatch.setenv("TEST_SERVER", "nats://test.example.com:4222")

    config_data = {
        "nats": {"servers": ["${TEST_SERVER}"]},
        "channels": [{"domain": "cytu.be", "channel": "lounge"}],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        config = KrytenConfig.from_json(temp_path)
        assert config.nats.servers[0] == "nats://test.example.com:4222"
    finally:
        Path(temp_path).unlink()


def test_kryten_config_from_json_missing_file():
    """Test error when JSON file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        KrytenConfig.from_json("nonexistent.json")
