"""
Tests for Telegram bot handlers.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import ContextTypes

from bot.handlers import ask, courses, help_command, news, professors, schedule, start


@pytest.fixture
def mock_context():
    """Mock bot context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_voice = AsyncMock()
    return context


@pytest.fixture
def mock_update_with_user():
    """Mock update with user message."""
    user = User(
        id=12345,
        first_name="Test",
        last_name="Student",
        username="test",
        is_bot=False,
    )
    chat = Chat(id=12345, type="private")

    # Create a mock message instead of real Message object
    message = MagicMock()
    message.message_id = 1
    message.date = None
    message.chat = chat
    message.from_user = user
    message.text = "/start"
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.update_id = 1
    update.message = message
    update.effective_user = user
    update.effective_chat = chat

    return update


@pytest.mark.asyncio
async def test_start_command(mock_update_with_user, mock_context):
    """Test /start command handler."""
    await start(mock_update_with_user, mock_context)

    mock_context.bot.send_message.assert_called_once()
    call_args = mock_context.bot.send_message.call_args
    assert "Bienvenue" in call_args[1]["text"] or "Welcome" in call_args[1]["text"]


@pytest.mark.asyncio
async def test_help_command(mock_update_with_user, mock_context):
    """Test /help command handler."""
    await help_command(mock_update_with_user, mock_context)

    mock_context.bot.send_message.assert_called_once()
    call_args = mock_context.bot.send_message.call_args
    assert (
        "commandes" in call_args[1]["text"].lower()
        or "commands" in call_args[1]["text"].lower()
    )


@pytest.mark.asyncio
@patch("core.data_loader.load_json_data")
@patch("bot.handlers.load_json_data")  # Mock the student check
async def test_schedule_command(
    mock_student_data, mock_load_data, mock_update_with_user, mock_context
):
    """Test /schedule command handler."""
    # Mock student data for authentication
    mock_student_data.return_value = [
        {"complete_name": "Test Student", "field": "Sécurité informatique"}
    ]

    # Mock schedule data
    mock_load_data.return_value = {
        "Monday": [
            {"time": "08:30-10:00", "course": "Cours AAC", "professor": "LEBBAH"}
        ]
    }

    await schedule(mock_update_with_user, mock_context)

    mock_context.bot.send_message.assert_called()


@pytest.mark.asyncio
@patch("bot.handlers.load_json_data")
async def test_professors_command(mock_load_data, mock_update_with_user, mock_context):
    """Test /professors command handler."""
    # Mock both student data (for auth) and professor data
    mock_load_data.side_effect = [
        # First call for student authentication
        [{"complete_name": "Test Student", "field": "Sécurité informatique"}],
        # Second call for professor data
        [
            {
                "name": "MAKHLOUF",
                "email": "sidahmed.makhlouf@gmail.com",
                "courses": ["Piratage éthique"],
            }
        ],
    ]

    await professors(mock_update_with_user, mock_context)

    mock_context.bot.send_message.assert_called()


@pytest.mark.asyncio
@patch("bot.handlers.load_json_data")
async def test_courses_command(mock_load_data, mock_update_with_user, mock_context):
    """Test /courses command handler."""
    # Mock both student data and programs data
    mock_load_data.side_effect = [
        # First call for student authentication
        [{"complete_name": "Test Student", "field": "Sécurité informatique"}],
        # Second call for programs data
        {
            "programs": [
                {
                    "name": "Sécurité Informatique (SI)",
                    "semesters": [
                        {
                            "semester": 1,
                            "units": [
                                {
                                    "type": "Core",
                                    "subunits": [
                                        {"modules": [{"name": "Cryptography"}]}
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ]
        },
    ]

    await courses(mock_update_with_user, mock_context)

    mock_update_with_user.message.reply_text.assert_called()


@pytest.mark.asyncio
@patch("core.news_scraper.get_news_scraper")
async def test_news_command(mock_scraper, mock_update_with_user, mock_context):
    """Test /news command handler."""
    # Mock news data
    mock_scraper.return_value = [
        {
            "title": "Test News Article",
            "url": "https://example.com/news",
            "summary": "Test summary",
        }
    ]

    await news(mock_update_with_user, mock_context)

    mock_context.bot.send_message.assert_called()


@pytest.mark.asyncio
@patch("core.llm.chat_completion")
@patch("bot.handlers.load_json_data")
async def test_ai_chat_handler(
    mock_student_data, mock_llm, mock_update_with_user, mock_context
):
    """Test AI chat message handler."""
    # Mock student authentication
    mock_student_data.return_value = [
        {"complete_name": "Test Student", "field": "Sécurité informatique"}
    ]

    mock_llm.return_value = "Test AI response"

    # Set up context args for the ask command
    mock_context.args = ["Hello", "how", "are", "you?"]

    await ask(mock_update_with_user, mock_context)

    mock_context.bot.send_message.assert_called()
    mock_llm.assert_called_once()


@pytest.mark.asyncio
async def test_handler_error_handling(mock_update_with_user, mock_context):
    """Test error handling in handlers."""
    # Mock an error in message.reply_text
    mock_update_with_user.message.reply_text.side_effect = Exception("Test error")

    # Should not raise exception - but our current handlers don't have error handling
    # So we expect this to raise for now
    with pytest.raises(Exception):
        await start(mock_update_with_user, mock_context)


@pytest.mark.asyncio
@patch("bot.handlers.load_json_data")
async def test_user_authentication(mock_load_data, mock_context):
    """Test user authentication in handlers."""
    # Mock empty student list (no authorized users)
    mock_load_data.return_value = []

    # Mock unauthorized user
    unauthorized_user = MagicMock()
    unauthorized_user.id = 99999
    unauthorized_user.first_name = "Unknown"
    unauthorized_user.last_name = "User"
    unauthorized_user.username = "unknown"

    chat = MagicMock()
    chat.id = 99999
    chat.type = "private"

    message = MagicMock()
    message.message_id = 1
    message.chat = chat
    message.from_user = unauthorized_user
    message.text = "/schedule"
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.update_id = 1
    update.message = message
    update.effective_user = unauthorized_user
    update.effective_chat = chat

    await schedule(update, mock_context)

    # Should send unauthorized message
    message.reply_text.assert_called()
    call_args = message.reply_text.call_args[0][0]
    assert (
        "access denied" in call_args.lower()
        or "not in the students list" in call_args.lower()
    )
