from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from core.config import Settings
from bot.handlers import (
    start,
    help_command,
    professors,
    courses,
    schedule,
    ask,
    voice,
    ask_voice,
    resources,
    examtips,
    tools,
    internships,
    thesis,
    events,
    faqs,
    deadlines,
    news,
    hackernews,
    technews,
    news_sources,
    my_news_profile,
    save_message,
)
from core.db import get_db

def create_bot_app(settings: Settings) -> Application:
    """Creates and configures the Telegram bot application."""
    application = Application.builder().token(settings.TELEGRAM_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("professors", professors))
    application.add_handler(CommandHandler("courses", courses))
    application.add_handler(CommandHandler("schedule", schedule))
    application.add_handler(CommandHandler("ask", ask))
    application.add_handler(CommandHandler("voice", voice))
    application.add_handler(CommandHandler("askvoice", ask_voice))
    application.add_handler(CommandHandler("resources", resources))
    application.add_handler(CommandHandler("examtips", examtips))
    application.add_handler(CommandHandler("tools", tools))
    application.add_handler(CommandHandler("internships", internships))
    application.add_handler(CommandHandler("thesis", thesis))
    application.add_handler(CommandHandler("events", events))
    application.add_handler(CommandHandler("faqs", faqs))
    application.add_handler(CommandHandler("deadlines", deadlines))
    application.add_handler(CommandHandler("news", news))
    application.add_handler(CommandHandler("hackernews", hackernews))
    application.add_handler(CommandHandler("technews", technews))
    application.add_handler(CommandHandler("news_sources", news_sources))
    application.add_handler(CommandHandler("mynews", my_news_profile))

    # Persist non-command text messages to MongoDB
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), save_message))

    return application
