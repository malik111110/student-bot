"""
Tests for main application startup behavior.
"""

import pytest
import os
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_app_startup_in_test_mode():
    """Test that the app can start in test mode without initializing the bot."""
    with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
        # Import after setting environment
        from main import app
        
        # Test that the app can be created without errors
        assert app is not None
        # Title will be different in test mode due to test configuration
        assert "Bot" in app.title


def test_health_check_endpoint():
    """Test the health check endpoint works."""
    with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
        from main import app
        
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_telegram_webhook_without_bot():
    """Test telegram webhook returns 503 when bot is not initialized."""
    with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
        from main import app
        
        with TestClient(app) as client:
            # Try to access webhook endpoint when bot is not initialized
            response = client.post("/telegram/webhook/test_token", json={"update_id": 1})
            assert response.status_code == 503
            assert "Bot not initialized" in response.json()["detail"]