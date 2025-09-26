import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers import (
    professors,
    check_student,
    start,
    help_command,
    courses,
    schedule,
    ask,
    resources,
    examtips,
    tools,
    internships,
    thesis,
    events,
    faqs,
    deadlines,
)

# Sample student data for mocking
MOCK_STUDENTS = [
    {"id": "01", "complete_name": "John Doe", "field": "Resin"},
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
async def test_check_student_decorator_authorized(mock_load_data, mock_update_context):
    """Test that the check_student decorator allows authorized users."""
    update, context = mock_update_context
    update.effective_user = MagicMock(first_name="John", last_name="Doe")

    @check_student
    async def dummy_handler(update, context):
        await update.message.reply_text("Success!")

    await dummy_handler(update, context)

    update.message.reply_text.assert_awaited_with("Success!")
    assert "student_info" in context.user_data
    assert context.user_data["student_info"]["complete_name"] == "John Doe"

@pytest.mark.asyncio
@patch('bot.handlers.load_json_data', return_value=MOCK_STUDENTS)
async def test_check_student_decorator_unauthorized(mock_load_data, mock_update_context):
    """Test that the check_student decorator blocks unauthorized users."""
    update, context = mock_update_context
    update.effective_user = MagicMock(first_name="Unknown", last_name="User")

    @check_student
    async def dummy_handler(update, context):
        # This part should not be executed
        await update.message.reply_text("This should not be sent.")

    await dummy_handler(update, context)

    update.message.reply_text.assert_awaited_with("Access denied. You are not in the students list. Please contact the admin.")

@pytest.mark.asyncio
async def test_start_command(mock_update_context):
    """Test the simplified start command."""
    update, context = mock_update_context
    await start(update, context)
    update.message.reply_text.assert_awaited_with("Welcome to the InfoSec Promo Bot!\nUse /help to see available commands.")

@pytest.mark.asyncio
async def test_help_command(mock_update_context):
    """Test the updated help command."""
    update, context = mock_update_context
    await help_command(update, context)
    update.message.reply_text.assert_awaited()
    call_args = update.message.reply_text.call_args[0][0]
    assert "/start" in call_args
    assert "/whoami" not in call_args
    assert "/logout" not in call_args

@pytest.mark.asyncio
@patch('bot.handlers.load_json_data')
async def test_professors_command_authorized(mock_load_data, mock_update_context):
    """Test the professors command with an authorized user."""
    mock_load_data.side_effect = [
        MOCK_STUDENTS,  # First call from check_student
        [{"name": "Test Prof", "email": "test@test.com"}]  # Second call from professors
    ]
    update, context = mock_update_context
    update.effective_user = MagicMock(first_name="John", last_name="Doe")

    await professors(update, context)

    context.bot.send_message.assert_awaited()
    call_args = context.bot.send_message.call_args[1]['text']
    assert "Professor Contacts" in call_args
    assert "Test Prof" in call_args

@pytest.mark.asyncio
@patch('bot.handlers.load_json_data', return_value=MOCK_STUDENTS)
async def test_check_student_decorator_case_insensitive(mock_load_data, mock_update_context):
    """Test that the check_student decorator is case-insensitive."""
    update, context = mock_update_context
    update.effective_user = MagicMock(first_name="jOhN", last_name="dOe")

    @check_student
    async def dummy_handler(update, context):
        await update.message.reply_text("Success!")

    await dummy_handler(update, context)

    update.message.reply_text.assert_awaited_with("Success!")
    assert "student_info" in context.user_data
    assert context.user_data["student_info"]["complete_name"] == "John Doe"

@pytest.mark.asyncio
@patch('bot.handlers.load_json_data')
async def test_courses_command_authorized(mock_load_data, mock_update_context):
    """Test the courses command with an authorized user."""
    mock_programs = {
        "programs": [
            {
                "name": "Réseaux et Systèmes d'Information (Resin)",
                "semesters": [
                    {
                        "semester": 1,
                        "units": [
                            {
                                "type": "UEF",
                                "subunits": [
                                    {
                                        "modules": [
                                            {"name": "Course 1"},
                                            {"name": "Course 2"},
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    mock_load_data.side_effect = [
        MOCK_STUDENTS,  # First call from check_student
        mock_programs  # Second call from courses
    ]
    update, context = mock_update_context
    update.effective_user = MagicMock(first_name="John", last_name="Doe")
    context.user_data = {"student_info": {"field": "Resin"}}


    await courses(update, context)

    update.message.reply_text.assert_awaited()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Courses for Réseaux et Systèmes d'Information (Resin)" in call_args
    assert "Course 1" in call_args
    assert "Course 2" in call_args

@pytest.mark.asyncio
@patch('bot.handlers.load_json_data')
async def test_schedule_command_authorized(mock_load_data, mock_update_context):
    """Test the schedule command with an authorized user."""
    mock_schedule = {
        "monday": [
            {"time": "09:00", "course": "Course 1", "professor": "Prof A"},
        ]
    }
    mock_load_data.side_effect = [
        MOCK_STUDENTS,  # First call from check_student
        mock_schedule  # Second call from schedule
    ]
    update, context = mock_update_context
    update.effective_user = MagicMock(first_name="John", last_name="Doe")

    await schedule(update, context)

    update.message.reply_text.assert_awaited()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Weekly Schedule" in call_args
    assert "Monday" in call_args
    assert "Course 1" in call_args

@pytest.mark.asyncio
@patch('bot.handlers.chat_completion', return_value="This is a test answer.")
@patch('bot.handlers.load_json_data', return_value=MOCK_STUDENTS)
async def test_ask_command_authorized(mock_load_data, mock_chat_completion, mock_update_context):
    """Test the ask command with an authorized user."""
    update, context = mock_update_context
    update.effective_user = MagicMock(first_name="John", last_name="Doe")
    context.args = ["what", "is", "love?"]

    await ask(update, context)

    context.bot.send_message.assert_awaited_with(chat_id=123, text="This is a test answer.")

@pytest.mark.asyncio
@patch('bot.handlers.load_json_data')
async def test_resources_command_authorized(mock_load_data, mock_update_context):
    """Test the resources command with an authorized user."""
    mock_resources = {"roadmaps": [{"name": "Test Roadmap", "url": "http://example.com"}]}
    mock_load_data.side_effect = [
        MOCK_STUDENTS,
        mock_resources
    ]
    update, context = mock_update_context
    update.effective_user = MagicMock(first_name="John", last_name="Doe")

    await resources(update, context)

    context.bot.send_message.assert_awaited()
    call_args = context.bot.send_message.call_args[1]['text']
    assert "Top Resources" in call_args
    assert "Test Roadmap" in call_args
