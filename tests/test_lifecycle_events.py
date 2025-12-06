"""Tests for lifecycle events module."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from kryten.lifecycle_events import LifecycleEventPublisher


@pytest.fixture
def mock_nats_client():
    """Create a mock NATS client."""
    client = AsyncMock()
    client.subscribe = AsyncMock()
    client.publish = AsyncMock()
    return client


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
async def lifecycle_publisher(mock_nats_client, mock_logger):
    """Create a lifecycle event publisher."""
    publisher = LifecycleEventPublisher(
        service_name="test_service",
        nats_client=mock_nats_client,
        logger=mock_logger,
        version="1.0.0"
    )
    yield publisher
    if publisher.is_running:
        await publisher.stop()


class TestLifecycleEventPublisher:
    """Test lifecycle event publisher functionality."""
    
    async def test_initialization(self, lifecycle_publisher):
        """Test publisher initialization."""
        assert lifecycle_publisher._service_name == "test_service"
        assert lifecycle_publisher._version == "1.0.0"
        assert not lifecycle_publisher.is_running
        assert lifecycle_publisher._hostname is not None
    
    async def test_start(self, lifecycle_publisher, mock_nats_client):
        """Test starting the publisher."""
        await lifecycle_publisher.start()
        
        assert lifecycle_publisher.is_running
        assert lifecycle_publisher._start_time is not None
        mock_nats_client.subscribe.assert_called_once_with(
            "kryten.lifecycle.group.restart",
            cb=lifecycle_publisher._handle_restart_notice
        )
    
    async def test_start_already_running(self, lifecycle_publisher, mock_logger):
        """Test starting when already running."""
        await lifecycle_publisher.start()
        await lifecycle_publisher.start()  # Second start
        
        mock_logger.warning.assert_called_with("Lifecycle event publisher already running")
    
    async def test_stop(self, lifecycle_publisher):
        """Test stopping the publisher."""
        mock_sub = AsyncMock()
        lifecycle_publisher._subscription = mock_sub
        lifecycle_publisher._running = True
        
        await lifecycle_publisher.stop()
        
        assert not lifecycle_publisher.is_running
        assert lifecycle_publisher._subscription is None
        mock_sub.unsubscribe.assert_called_once()
    
    async def test_publish_startup(self, lifecycle_publisher, mock_nats_client, mock_logger):
        """Test publishing startup event."""
        await lifecycle_publisher.start()
        await lifecycle_publisher.publish_startup(domain="cytu.be", channel="test")
        
        # Check publish was called
        assert mock_nats_client.publish.called
        call_args = mock_nats_client.publish.call_args
        subject = call_args[0][0]
        data = json.loads(call_args[0][1].decode('utf-8'))
        
        assert subject == "kryten.lifecycle.test_service.startup"
        assert data["service"] == "test_service"
        assert data["version"] == "1.0.0"
        assert data["domain"] == "cytu.be"
        assert data["channel"] == "test"
        assert "timestamp" in data
        assert "hostname" in data
    
    async def test_publish_shutdown(self, lifecycle_publisher, mock_nats_client):
        """Test publishing shutdown event."""
        await lifecycle_publisher.start()
        await lifecycle_publisher.publish_shutdown(reason="Test shutdown")
        
        call_args = mock_nats_client.publish.call_args
        subject = call_args[0][0]
        data = json.loads(call_args[0][1].decode('utf-8'))
        
        assert subject == "kryten.lifecycle.test_service.shutdown"
        assert data["reason"] == "Test shutdown"
    
    async def test_publish_connected(self, lifecycle_publisher, mock_nats_client):
        """Test publishing connected event."""
        await lifecycle_publisher.start()
        await lifecycle_publisher.publish_connected("NATS", servers=["nats://localhost:4222"])
        
        call_args = mock_nats_client.publish.call_args
        subject = call_args[0][0]
        data = json.loads(call_args[0][1].decode('utf-8'))
        
        assert subject == "kryten.lifecycle.test_service.connected"
        assert data["target"] == "NATS"
        assert data["servers"] == ["nats://localhost:4222"]
    
    async def test_publish_disconnected(self, lifecycle_publisher, mock_nats_client):
        """Test publishing disconnected event."""
        await lifecycle_publisher.start()
        await lifecycle_publisher.publish_disconnected("CyTube", reason="Connection lost")
        
        call_args = mock_nats_client.publish.call_args
        subject = call_args[0][0]
        data = json.loads(call_args[0][1].decode('utf-8'))
        
        assert subject == "kryten.lifecycle.test_service.disconnected"
        assert data["target"] == "CyTube"
        assert data["reason"] == "Connection lost"
    
    async def test_publish_group_restart(self, lifecycle_publisher, mock_nats_client):
        """Test publishing groupwide restart notice."""
        await lifecycle_publisher.start()
        await lifecycle_publisher.publish_group_restart(
            reason="Config update",
            delay_seconds=10,
            initiator="admin"
        )
        
        call_args = mock_nats_client.publish.call_args
        subject = call_args[0][0]
        data = json.loads(call_args[0][1].decode('utf-8'))
        
        assert subject == "kryten.lifecycle.group.restart"
        assert data["reason"] == "Config update"
        assert data["delay_seconds"] == 10
        assert data["initiator"] == "admin"
    
    async def test_restart_callback(self, lifecycle_publisher):
        """Test restart notice callback."""
        callback_called = False
        callback_data = None
        
        async def restart_callback(data):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data
        
        lifecycle_publisher.on_restart_notice(restart_callback)
        await lifecycle_publisher.start()
        
        # Simulate restart notice
        msg = Mock()
        msg.data = json.dumps({
            "initiator": "test",
            "reason": "Test restart",
            "delay_seconds": 5
        }).encode('utf-8')
        
        await lifecycle_publisher._handle_restart_notice(msg)
        
        assert callback_called
        assert callback_data["reason"] == "Test restart"
    
    async def test_handle_invalid_restart_notice(self, lifecycle_publisher, mock_logger):
        """Test handling invalid restart notice JSON."""
        await lifecycle_publisher.start()
        
        msg = Mock()
        msg.data = b"invalid json"
        
        await lifecycle_publisher._handle_restart_notice(msg)
        
        # Should log error but not crash
        assert mock_logger.error.called
    
    async def test_uptime_calculation(self, lifecycle_publisher, mock_nats_client):
        """Test that uptime is calculated correctly."""
        await lifecycle_publisher.start()
        
        # Wait a bit
        await asyncio.sleep(0.1)
        
        await lifecycle_publisher.publish_shutdown()
        
        call_args = mock_nats_client.publish.call_args
        data = json.loads(call_args[0][1].decode('utf-8'))
        
        assert data["uptime_seconds"] is not None
        assert data["uptime_seconds"] >= 0.1
