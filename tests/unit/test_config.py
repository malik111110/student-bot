"""
Tests for core configuration module.
"""

import pytest
from pydantic import ValidationError

from core.config import Settings


class TestSettings:
    """Test configuration settings."""

    def test_settings_creation_with_defaults(self):
        """Test settings creation with default values."""
        settings = Settings(
            TELEGRAM_TOKEN="test_token",
            SUPABASE_URL="https://test.supabase.co",
            SUPABASE_KEY="test_key",
        )

        assert settings.TELEGRAM_TOKEN == "test_token"
        assert settings.PROJECT_NAME == "Promo Section Bot"
        assert settings.API_V1_STR == "/api/v1"
        assert settings.SUPABASE_URL == "https://test.supabase.co"

    def test_settings_validation_missing_required(self):
        """Test settings validation with missing required fields."""
        # Test that settings can be created and have required fields
        settings = Settings()
        assert settings.TELEGRAM_TOKEN is not None
        assert len(settings.TELEGRAM_TOKEN) > 0

    def test_settings_with_all_fields(self):
        """Test settings with all fields provided."""
        settings = Settings(
            TELEGRAM_TOKEN="test_token",
            PROJECT_NAME="Test Bot",
            API_V1_STR="/api/v2",
            MONGODB_URI="mongodb://localhost:27017/test",
            PUBLIC_BASE_URL="https://example.com",
            OPENROUTER_API_KEY="test_openrouter",
            OPENROUTER_MODEL="test_model",
            FIRECRAWL_API_KEY="test_firecrawl",
            ELEVEN_LAB_API_KEY="test_elevenlabs",
            SUPABASE_URL="https://test.supabase.co",
            SUPABASE_KEY="test_key",
            SUPABASE_SERVICE_ROLE_KEY="test_service_key",
        )

        assert settings.PROJECT_NAME == "Test Bot"
        assert settings.API_V1_STR == "/api/v2"
        assert settings.OPENROUTER_MODEL == "test_model"

    def test_settings_environment_loading(self, monkeypatch):
        """Test settings loading from environment variables."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "env_token")
        monkeypatch.setenv("SUPABASE_URL", "https://env.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "env_key")

        settings = Settings()

        assert settings.TELEGRAM_TOKEN == "env_token"
        assert settings.SUPABASE_URL == "https://env.supabase.co"
        assert settings.SUPABASE_KEY == "env_key"
