
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers import news, hackernews, technews, news_sources, my_news_profile

# Sample student data for mocking
MOCK_STUDENTS = [
    {"id": "01", "complete_name": "John Doe", "field": "Sécurité informatique"},
    {"id": "02", "complete_name": "Jane Smith", "field": "RSD"},
]

@pytest.fixture
def mock_update_context():
    """Fixture to create mock update and context objects."""
    update = MagicMock()
    update.message = AsyncMock()
    update.effective_chat = MagicMock()
    update.effective_chat.id = 123
    
    context = AsyncMock()
    context.bot = AsyncMock()
    context.user_data = {}
    context.args = []

    return update, context

@pytest.mark.asyncio
@patch('bot.handlers.load_json_data', return_value=MOCK_STUDENTS)
@patch('bot.handlers.get_news_scraper')
async def test_my_news_profile_authorized(mock_get_scraper, mock_load_data, mock_update_context):
    """Test the my_news_profile command with an authorized user."""
    update, context = mock_update_context
    update.effective_user = MagicMock(first_name="John", last_name="Doe")
    context.user_data = {"student_info": MOCK_STUDENTS[0]}

    mock_scraper = MagicMock()
    mock_scraper.get_field_keywords.return_value = ["cybersecurity", "infosec", "hacking"]
    mock_scraper._get_field_emoji.return_value = "🛡️"
    mock_get_scraper.return_value = mock_scraper

    await my_news_profile(update, context)

    context.bot.send_message.assert_awaited()
    call_args = context.bot.send_message.call_args[1]['text']
    assert "Your Personalized News Profile" in call_args
    assert "John Doe" in call_args
    assert "Sécurité informatique" in call_args
    assert "cybersecurity, infosec, hacking" in call_args

@pytest.mark.asyncio
@patch('bot.handlers.load_json_data', return_value=MOCK_STUDENTS)
@patch('bot.handlers.get_news_scraper')
async def test_news_command_authorized(mock_get_scraper, mock_load_data, mock_update_context):
    """Test the news command with an authorized user."""
    update, context = mock_update_context
    update.effective_user = MagicMock(first_name="John", last_name="Doe")
    context.user_data = {"student_info": MOCK_STUDENTS[0]}

    mock_scraper = AsyncMock()
    mock_scraper.get_personalized_news.return_value = {"success": True, "content": "Personalized news content"}
    mock_scraper.format_news_for_telegram.return_value = "Formatted news"
    mock_get_scraper.return_value = mock_scraper

    await news(update, context)

    context.bot.send_message.assert_awaited()
    # Check the "Fetching personalized news" message
    assert "Fetching personalized news" in context.bot.send_message.call_args_list[0][1]['text']
    # Check the final news message
    assert "Formatted news" in context.bot.send_message.call_args_list[1][1]['text']

@pytest.mark.asyncio
@patch('bot.handlers.get_news_scraper')
async def test_hackernews_command(mock_get_scraper, mock_update_context):
    """Test the hackernews command."""
    update, context = mock_update_context

    mock_scraper = AsyncMock()
    mock_scraper.get_hacker_news.return_value = {"success": True, "content": "Hacker news content"}
    mock_scraper.format_news_for_telegram.return_value = "Formatted hacker news"
    mock_get_scraper.return_value = mock_scraper

    await hackernews(update, context)

    context.bot.send_message.assert_awaited()
    assert "Formatted hacker news" in context.bot.send_message.call_args[1]['text']

@pytest.mark.asyncio
@patch('bot.handlers.load_json_data', return_value=MOCK_STUDENTS)
@patch('bot.handlers.get_news_scraper')
async def test_technews_command_with_source(mock_get_scraper, mock_load_data, mock_update_context):
    """Test the technews command with a specific source."""
    update, context = mock_update_context
    update.effective_user = MagicMock(first_name="John", last_name="Doe")
    context.user_data = {"student_info": MOCK_STUDENTS[0]}
    context.args = ["techcrunch"]

    mock_scraper = AsyncMock()
    mock_scraper.get_available_sources.return_value = {"techcrunch": {"name": "TechCrunch", "description": "Tech news"}}
    mock_scraper.get_tech_news.return_value = {"success": True, "content": "TechCrunch news"}
    mock_scraper.format_news_for_telegram.return_value = "Formatted TechCrunch news"
    mock_get_scraper.return_value = mock_scraper

    await technews(update, context)

    context.bot.send_message.assert_awaited()
    assert "Formatted TechCrunch news" in context.bot.send_message.call_args[1]['text']

@pytest.mark.asyncio
@patch('bot.handlers.get_news_scraper')
async def test_news_sources_command(mock_get_scraper, mock_update_context):
    """Test the news_sources command."""
    update, context = mock_update_context

    mock_scraper = MagicMock()
    mock_scraper.get_available_sources.return_value = {
        "techcrunch": {"name": "TechCrunch", "description": "Tech news"},
        "wired": {"name": "Wired", "description": "Tech and culture"}
    }
    mock_get_scraper.return_value = mock_scraper

    await news_sources(update, context)

    context.bot.send_message.assert_awaited()
    call_args = context.bot.send_message.call_args[1]['text']
    assert "Available News Sources" in call_args
    assert "TechCrunch" in call_args
    assert "Wired" in call_args
