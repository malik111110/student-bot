"""
Pytest configuration and fixtures for InfoSec Bot tests.
"""
import os
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from telegram import Bot, Update, Message, User, Chat
from telegram.ext import Application

# Set test environment before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["DISABLE_EXTERNAL_CALLS"] = "true"

from main import app
from core.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test settings with mock values."""
    return Settings(
        TELEGRAM_TOKEN="test_token",
        PROJECT_NAME="Test InfoSec Bot",
        MONGODB_URI="mongodb://localhost:27017/test",
        SUPABASE_URL="https://test.supabase.co",
        SUPABASE_KEY="test_key",
        SUPABASE_SERVICE_ROLE_KEY="test_service_key",
        OPENROUTER_API_KEY="test_key",
        FIRECRAWL_API_KEY="test_key",
        ELEVEN_LAB_API_KEY="test_key",
        API_V1_STR="/api/v1",
        ENVIRONMENT="test",
        DISABLE_EXTERNAL_CALLS=True
    )


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_bot():
    """Mock Telegram bot."""
    bot = MagicMock(spec=Bot)
    bot.token = "test_token"
    bot.get_me = AsyncMock(return_value=User(
        id=123456789,
        first_name="InfoSec",
        last_name="Bot",
        username="infosec_bot",
        is_bot=True
    ))
    bot.set_webhook = AsyncMock()
    bot.delete_webhook = AsyncMock()
    bot.get_webhook_info = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_voice = AsyncMock()
    return bot


@pytest.fixture
def mock_application(mock_bot):
    """Mock Telegram application."""
    app = MagicMock(spec=Application)
    app.bot = mock_bot
    app.initialize = AsyncMock()
    app.start = AsyncMock()
    app.stop = AsyncMock()
    app.shutdown = AsyncMock()
    app.process_update = AsyncMock()
    return app


@pytest.fixture
def mock_user():
    """Mock Telegram user."""
    return User(
        id=12345,
        first_name="Test",
        last_name="Student",
        username="test_student",
        is_bot=False
    )


@pytest.fixture
def mock_chat():
    """Mock Telegram chat."""
    return Chat(
        id=12345,
        type="private"
    )


@pytest.fixture
def mock_message(mock_user, mock_chat):
    """Mock Telegram message."""
    return Message(
        message_id=1,
        date=None,
        chat=mock_chat,
        from_user=mock_user,
        text="/start"
    )


@pytest.fixture
def mock_update(mock_message):
    """Mock Telegram update."""
    return Update(
        update_id=1,
        message=mock_message
    )


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    client = MagicMock()
    client.table = MagicMock()
    client.table.return_value.select = MagicMock()
    client.table.return_value.insert = MagicMock()
    client.table.return_value.update = MagicMock()
    client.table.return_value.delete = MagicMock()
    return client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock()
    return client


@pytest.fixture
def sample_student_data():
    """Sample student data for testing."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "student_number": "INFOSEC01",
        "first_name": "Test",
        "last_name": "Student",
        "email": "test.student@university.edu",
        "field_of_study_id": "456e7890-e89b-12d3-a456-426614174001",
        "academic_year": 1,
        "telegram_id": 12345,
        "telegram_username": "test_student",
        "status": "active"
    }


@pytest.fixture
def sample_course_data():
    """Sample course data for testing."""
    return {
        "id": "789e0123-e89b-12d3-a456-426614174002",
        "code": "INFOSEC_CRYPTO",
        "name": "Cryptography and Security",
        "description": "Advanced cryptography course",
        "credits": 5,
        "field_of_study_id": "456e7890-e89b-12d3-a456-426614174001",
        "academic_year": 1,
        "semester": 1,
        "is_active": True
    }


@pytest.fixture
def sample_professor_data():
    """Sample professor data for testing."""
    return {
        "id": "abc1234-e89b-12d3-a456-426614174003",
        "first_name": "Dr. John",
        "last_name": "Smith",
        "email": "john.smith@university.edu",
        "title": "Professor",
        "department": "Computer Science"
    }


@pytest.fixture
def sample_schedule_data():
    """Sample schedule data for testing."""
    return {
        "id": "def5678-e89b-12d3-a456-426614174004",
        "course_assignment_id": "ghi9012-e89b-12d3-a456-426614174005",
        "classroom_id": "jkl3456-e89b-12d3-a456-426614174006",
        "session_date": "2025-09-07",
        "time_slot_id": "mno7890-e89b-12d3-a456-426614174007",
        "session_type": "lecture",
        "title": "Introduction to Cryptography",
        "is_recurring": True,
        "recurrence_pattern": "weekly",
        "status": "scheduled"
    }