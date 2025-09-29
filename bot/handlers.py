import inspect
from datetime import datetime, timezone
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from core.config import settings
from core.data_loader import load_json_data
from core.db import get_db
from core.llm import chat_completion
from core.message_formatter import format_ai_response, format_voice_text
from core.news_scraper import get_news_scraper
from core.tts import get_tts_service


def get_program_name(field: str) -> str | None:
    """Maps a student's field to a program name."""
    mapping = {
        "Sécurité informatique": "Sécurité Informatique (SI)",
        "Intelligence Artificielle": "Intelligence Artificielle (IA)",
        "RSD": "Réseaux et Systèmes Distribués (RSD)",
        "Sciences des Données": "Science des Données (SD)",
        "Resin": "Réseaux et Systèmes d'Information (Resin)",
    }
    return mapping.get(field)


def check_student(func):
    @wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user = update.effective_user
        if not user:
            await update.message.reply_text("Could not identify user.")
            return

        # Construct user's full name
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        user_full_name = f"{first_name} {last_name}".strip()

        students = load_json_data("students.json")

        # Try exact match first (case insensitive)
        student_info = next(
            (
                s
                for s in students
                if s.get("complete_name", "").lower() == user_full_name.lower()
            ),
            None,
        )

        # If no exact match, try partial matching
        if not student_info:
            # Check if the user's name parts are contained in any student name
            first_lower = first_name.lower()
            last_lower = last_name.lower()

            for student in students:
                complete_name_lower = student.get("complete_name", "").lower()
                # Check if both first and last name are in the complete name
                if (
                    first_lower in complete_name_lower
                    and last_lower in complete_name_lower
                ):
                    student_info = student
                    break

        if student_info:
            # Store student_info in user_data for other commands to use
            context.user_data["student_info"] = student_info
            return await func(update, context, *args, **kwargs)
        else:
            await update.message.reply_text(
                "Access denied. You are not in the students list. Please contact the admin."
            )
            return

    return wrapper


async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Saves incoming messages to MongoDB or local file as fallback."""
    try:
        message = update.message
        if not message:
            return

        chat = update.effective_chat
        user = update.effective_user

        if not chat or not user:
            return

        # Skip saving if MongoDB is not configured
        if not settings.MONGODB_URI:
            return

        # Create message data
        message_data = {
            "chat_id": chat.id,
            "chat_type": chat.type,
            "user_id": user.id,
            "text": message.text,
            "date": datetime.now(timezone.utc),
        }

        # Try MongoDB first
        try:
            db = get_db()
            result = db.messages.insert_one(message_data)
            print(f"✅ Message saved to MongoDB with ID: {result.inserted_id}")
        except Exception as db_error:
            # Fallback to local file logging
            print(f"⚠️ MongoDB failed, using local file fallback: {db_error}")

            # Save to local JSON file as backup
            import json
            import os

            log_file = "message_backup.jsonl"
            # Create a copy for JSON serialization to avoid modifying original
            json_data = message_data.copy()
            json_data["date"] = json_data["date"].isoformat()  # Make JSON serializable

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(json_data) + "\n")

            print(f"📝 Message saved to local file: {log_file}")

    except Exception as e:
        print(f"❌ Complete message saving failure: {e}")
        # Don't crash the bot - just continue without saving


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message."""
    welcome_text = (
        "Welcome to the InfoSec Promo Bot!\nUse /help to see available commands."
    )
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a list of available commands."""
    help_text = (
        "Available commands:\n"
        "/start - Show welcome message\n"
        "/help - Show this message\n"
        "/professors - List professor contacts\n"
        "/courses - List all courses\n"
        "/schedule - Show the weekly schedule\n"
        "/ask - Ask AI assistant a question\n"
        "/askvoice - Ask AI with voice response\n"
        "/voice - Convert text to voice message\n"
        "/resources - Study resources and tools\n"
        "/examtips - Exam preparation tips\n"
        "/news - Get personalized news for your field\n"
        "/hackernews - Get Hacker News\n"
        "/technews - Get personalized tech news\n"
        "/news_sources - List available news sources\n"
        "/my_news_profile - Show your news profile"
    )
    await update.message.reply_text(help_text)


@check_student
async def professors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and lists professors."""
    chat_id = update.effective_chat.id if update.effective_chat else None
    data = load_json_data("professors.json")
    if not isinstance(data, list) or not data:
        if chat_id:
            await context.bot.send_message(
                chat_id=chat_id, text="Could not retrieve professor data."
            )
        return

    lines = ["Professor Contacts:\n"]
    for prof in data:
        try:
            name = prof.get("name", "")
            email = prof.get("email", "")
            phone = prof.get("phone", "")
            courses = prof.get("courses", []) or []

            entry_lines = [f"👤 {name}", f"📧 {email}"]
            if phone:
                entry_lines.append(f"📞 {phone}")
            if courses:
                entry_lines.append(f"📘 Cours: {', '.join(courses)}")
            lines.append("\n".join(entry_lines) + "\n")
        except Exception:
            # Skip malformed entries silently
            continue

    # Send in chunks to avoid Telegram 4096 char limit
    text = "\n".join(lines)
    if not chat_id:
        return
    MAX_LEN = 4000
    start = 0
    while start < len(text):
        chunk = text[start : start + MAX_LEN]
        await context.bot.send_message(chat_id=chat_id, text=chunk)
        start += MAX_LEN


@check_student
async def courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and lists courses based on the user's field of study."""
    user_data = context.user_data
    programs_data = load_json_data("programs.json")

    # Handle `/courses all`
    if context.args and context.args[0].lower() == "all":
        all_courses = []
        for program in programs_data.get("programs", []):
            for semester in program.get("semesters", []):
                for unit in semester.get("units", []):
                    for subunit in unit.get("subunits", []):
                        for module in subunit.get("modules", []):
                            all_courses.append(module["name"])

        # Remove duplicates and sort
        unique_courses = sorted(list(set(all_courses)))

        message = "All Available Courses:\n\n"
        for course_name in unique_courses:
            message += f"📚 {course_name}\n"

        await update.message.reply_text(message)
        return

    student_info = user_data["student_info"]
    field = student_info.get("field")
    program_name = get_program_name(field)

    if not program_name:
        await update.message.reply_text("Could not determine your program of study.")
        return

    program = next(
        (p for p in programs_data.get("programs", []) if p.get("name") == program_name),
        None,
    )

    if not program:
        await update.message.reply_text(f"Could not find your program: {program_name}")
        return

    message = f"Courses for {program_name}:\n\n"
    for semester in program.get("semesters", []):
        message += f"--- Semester {semester['semester']} ---\n"
        for unit in semester.get("units", []):
            message += f"  {unit['type']}\n"
            for subunit in unit.get("subunits", []):
                for module in subunit.get("modules", []):
                    message += f"    - 📚 {module['name']}\n"
        message += "\n"

    # Send in chunks
    MAX_LEN = 4000
    start = 0
    while start < len(message):
        chunk = message[start : start + MAX_LEN]
        await update.message.reply_text(chunk)
        start += MAX_LEN


@check_student
async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and displays the weekly schedule based on student's field."""
    data = load_json_data("schedule.json")
    if not data:
        await update.message.reply_text("Could not retrieve schedule data.")
        return

    # Get student's field from user data
    student_info = context.user_data.get("student_info", {})
    field = student_info.get("field", "")

    # Map field to schedule key
    field_mapping = {
        "Sécurité informatique": "securite_informatique",
        "Intelligence Artificielle": "intelligence_artificielle",
        "Sciences des Données": "data_science",
        "RSD": "RSD",
        "Resin": "resin",
    }

    schedule_key = field_mapping.get(field)

    if not schedule_key or schedule_key not in data:
        # Show all available programs if field not found
        available_programs = list(data.keys())
        message = f"Schedule not found for your field: {field}\n\n"
        message += "Available programs:\n"
        for program in available_programs:
            message += f"- {program.replace('_', ' ').title()}\n"
        await update.message.reply_text(message)
        return

    program_schedule = data[schedule_key]
    program_name = schedule_key.replace("_", " ").title()

    message = f"📅 Weekly Schedule - {program_name}:\n\n"

    # Days in order
    days_order = ["saturday", "sunday", "monday", "tuesday", "wednesday", "thursday"]
    day_names = {
        "saturday": "Saturday",
        "sunday": "Sunday",
        "monday": "Monday",
        "tuesday": "Tuesday",
        "wednesday": "Wednesday",
        "thursday": "Thursday",
    }

    for day in days_order:
        if day in program_schedule:
            classes = program_schedule[day]
            message += f"🗓️ {day_names[day]}:\n"

            if not classes:
                message += "  No classes scheduled\n"
            else:
                for item in classes:
                    time = item.get("time", "TBD")
                    course = item.get("course", "Unknown Course")
                    professor = item.get("professor", "TBD")
                    room = item.get("room", "")

                    prof_text = f" ({professor})" if professor else ""
                    room_text = f" - {room}" if room else ""

                    message += f"  ⏰ {time}: {course}{prof_text}{room_text}\n"
            message += "\n"

    # Send in chunks if too long
    MAX_LEN = 4000
    start = 0
    while start < len(message):
        chunk = message[start : start + MAX_LEN]
        await update.message.reply_text(chunk)
        start += MAX_LEN


@check_student
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """LLM Q&A via OpenRouter. Usage: /ask <your question>"""
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return
    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /ask <your question>\nExample: /ask What is machine learning?",
        )
        return

    question = " ".join(context.args).strip()

    # Send "thinking" message
    thinking_msg = await context.bot.send_message(
        chat_id=chat_id, text="🤔 Thinking..."
    )

    try:
        reply = await chat_completion(
            [
                {"role": "user", "content": question},
            ]
        )

        # Delete the thinking message and send the response
        await context.bot.delete_message(
            chat_id=chat_id, message_id=thinking_msg.message_id
        )

        if reply:
            # Format the AI response for better UI/UX
            formatted_reply = format_ai_response(reply)

            # Split long responses into chunks if needed
            MAX_LEN = 4000
            if len(formatted_reply) <= MAX_LEN:
                await context.bot.send_message(chat_id=chat_id, text=formatted_reply)
            else:
                # Send in chunks
                start = 0
                while start < len(formatted_reply):
                    chunk = formatted_reply[start : start + MAX_LEN]
                    await context.bot.send_message(chat_id=chat_id, text=chunk)
                    start += MAX_LEN
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="I received an empty response. Please try rephrasing your question.",
            )

    except Exception as e:
        # Delete the thinking message
        try:
            await context.bot.delete_message(
                chat_id=chat_id, message_id=thinking_msg.message_id
            )
        except:
            pass

        print(f"LLM error: {e}")
        error_msg = "Sorry, I'm having trouble processing your request right now. "

        # Provide specific error messages for common issues
        if "rate" in str(e).lower() or "429" in str(e):
            error_msg += (
                "The AI service is temporarily busy. Please try again in a few moments."
            )
        elif "401" in str(e) or "unauthorized" in str(e).lower():
            error_msg += "There's an authentication issue with the AI service."
        elif "timeout" in str(e).lower():
            error_msg += "The request timed out. Please try a shorter question."
        else:
            error_msg += (
                "Please try again later or contact support if the issue persists."
            )

        await context.bot.send_message(chat_id=chat_id, text=error_msg)


@check_student
async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Convert text to voice message using ElevenLabs. Usage: /voice <text>"""
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return

    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /voice <text>\nExample: /voice Hello, this is a voice message!",
        )
        return

    text = " ".join(context.args).strip()
    tts_service = get_tts_service()

    if not tts_service.is_available():
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Voice service is not available. Please check the ElevenLabs API configuration.",
        )
        return

    # Send "generating" message
    generating_msg = await context.bot.send_message(
        chat_id=chat_id, text="🎤 Generating voice message..."
    )

    try:
        # Format text for voice synthesis
        voice_text = format_voice_text(text)

        # Convert text to speech
        audio_bytes = await tts_service.text_to_speech(voice_text)

        if audio_bytes:
            # Delete the generating message
            await context.bot.delete_message(
                chat_id=chat_id, message_id=generating_msg.message_id
            )

            # Send voice message
            import io

            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "voice_message.mp3"

            await context.bot.send_voice(
                chat_id=chat_id,
                voice=audio_file,
                caption=f"🎤 Voice: {text[:100]}{'...' if len(text) > 100 else ''}",
            )
        else:
            # Delete the generating message and send error
            await context.bot.delete_message(
                chat_id=chat_id, message_id=generating_msg.message_id
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Failed to generate voice message. Please try again.",
            )

    except Exception as e:
        # Delete the generating message
        try:
            await context.bot.delete_message(
                chat_id=chat_id, message_id=generating_msg.message_id
            )
        except:
            pass

        print(f"Voice generation error: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Error generating voice message. Please try again later.",
        )


@check_student
async def ask_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """AI Q&A with voice response. Usage: /askvoice <question>"""
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return

    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /askvoice <question>\nExample: /askvoice What is machine learning?",
        )
        return

    question = " ".join(context.args).strip()
    tts_service = get_tts_service()

    # Send "thinking" message
    thinking_msg = await context.bot.send_message(
        chat_id=chat_id, text="🤔 Thinking and preparing voice response..."
    )

    try:
        # Get AI response
        reply = await chat_completion(
            [
                {"role": "user", "content": question},
            ]
        )

        if not reply:
            await context.bot.delete_message(
                chat_id=chat_id, message_id=thinking_msg.message_id
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text="I received an empty response. Please try rephrasing your question.",
            )
            return

        # Format the AI response for better UI/UX
        formatted_reply = format_ai_response(reply)

        # Send text response first
        await context.bot.delete_message(
            chat_id=chat_id, message_id=thinking_msg.message_id
        )

        # Send formatted text response
        if len(formatted_reply) <= 4000:
            text_msg = await context.bot.send_message(
                chat_id=chat_id, text=formatted_reply
            )
        else:
            # Send in chunks for long responses
            chunks = [
                formatted_reply[i : i + 4000]
                for i in range(0, len(formatted_reply), 4000)
            ]
            for chunk in chunks:
                await context.bot.send_message(chat_id=chat_id, text=chunk)
            text_msg = None

        # Generate voice if TTS is available
        if tts_service.is_available():
            voice_msg = await context.bot.send_message(
                chat_id=chat_id, text="🎤 Generating voice response..."
            )

            # Prepare text for voice (limit length and format for speech)
            voice_text = reply[:500] + "..." if len(reply) > 500 else reply
            voice_text = format_voice_text(voice_text)
            audio_bytes = await tts_service.text_to_speech(voice_text)

            if audio_bytes:
                await context.bot.delete_message(
                    chat_id=chat_id, message_id=voice_msg.message_id
                )

                import io

                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = "ai_response.mp3"

                await context.bot.send_voice(
                    chat_id=chat_id, voice=audio_file, caption="🤖 AI Voice Response"
                )
            else:
                await context.bot.delete_message(
                    chat_id=chat_id, message_id=voice_msg.message_id
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="📝 Text response sent (voice generation failed)",
                )

    except Exception as e:
        # Delete the thinking message
        try:
            await context.bot.delete_message(
                chat_id=chat_id, message_id=thinking_msg.message_id
            )
        except:
            pass

        print(f"Ask voice error: {e}")
        error_msg = "Sorry, I'm having trouble processing your request right now. "

        if "rate" in str(e).lower() or "429" in str(e):
            error_msg += (
                "The AI service is temporarily busy. Please try again in a few moments."
            )
        elif "401" in str(e) or "unauthorized" in str(e).lower():
            error_msg += "There's an authentication issue with the AI service."
        else:
            error_msg += "Please try again later or use /ask for text-only responses."

        await context.bot.send_message(chat_id=chat_id, text=error_msg)


# --- Extra student-friendly helpers for InfoSec Master's students ---
@check_student
async def resources(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return
    data = load_json_data("resources.json")
    if not isinstance(data, dict):
        await context.bot.send_message(
            chat_id=chat_id, text="Could not load resources."
        )
        return
    lines = ["Top Resources for InfoSec MSc:\n"]
    if data.get("roadmaps"):
        lines.append("🧠 Roadmaps:")
        for r in data["roadmaps"]:
            name = r.get("name", "Roadmap")
            url = r.get("url", "")
            lines.append(f"- {name}: {url}")
        lines.append("")
    if data.get("reading"):
        lines.append("📚 Reading:")
        for item in data["reading"]:
            lines.append(f"- {item}")
        lines.append("")
    if data.get("labs"):
        lines.append("🧪 Labs:")
        for item in data["labs"]:
            lines.append(f"- {item}")
        lines.append("")
    if data.get("tools"):
        lines.append("🧰 Tools:")
        for item in data["tools"]:
            lines.append(f"- {item}")
        lines.append("")
    if data.get("papers"):
        lines.append("🎓 Papers:")
        for item in data["papers"]:
            lines.append(f"- {item}")
        lines.append("")
    if data.get("feeds"):
        lines.append("📰 Feeds:")
        for item in data["feeds"]:
            lines.append(f"- {item}")
        lines.append("")
    text = "\n".join(lines)
    await context.bot.send_message(chat_id=chat_id, text=text)


@check_student
async def examtips(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return
    tips = load_json_data("examtips.json")
    if not isinstance(tips, list) or not tips:
        await context.bot.send_message(chat_id=chat_id, text="No exam tips available.")
        return
    lines = ["Exam Tips (concise + effective):\n"]
    for t in tips:
        lines.append(f"- {t}")
    text = "\n".join(lines)
    await context.bot.send_message(chat_id=chat_id, text=text)


@check_student
async def tools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return
    data = load_json_data("tools.json")
    if not isinstance(data, dict):
        await context.bot.send_message(chat_id=chat_id, text="No tools data available.")
        return
    lines = ["Essential Tools by Area:\n"]
    for section, items in data.items():
        pretty = section.capitalize()
        joined = ", ".join(items)
        lines.append(f"- {pretty}: {joined}")
    text = "\n".join(lines)
    await context.bot.send_message(chat_id=chat_id, text=text)


@check_student
async def internships(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return
    items = load_json_data("internships.json")
    if not isinstance(items, list) or not items:
        await context.bot.send_message(
            chat_id=chat_id, text="No internship tips available."
        )
        return
    lines = ["Internship Strategy (fast + realistic):\n"]
    for i, tip in enumerate(items, start=1):
        lines.append(f"{i}) {tip}")
    text = "\n".join(lines)
    await context.bot.send_message(chat_id=chat_id, text=text)


@check_student
async def thesis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return
    items = load_json_data("thesis.json")
    if not isinstance(items, list) or not items:
        await context.bot.send_message(
            chat_id=chat_id, text="No thesis guidance available."
        )
        return
    lines = ["Thesis Blueprint:\n"]
    for item in items:
        lines.append(f"- {item}")
    text = "\n".join(lines)
    await context.bot.send_message(chat_id=chat_id, text=text)


@check_student
async def events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return
    data = load_json_data("events.json")
    if not isinstance(data, dict):
        await context.bot.send_message(
            chat_id=chat_id, text="No events data available."
        )
        return
    lines = ["Stay In The Loop:\n"]
    for section, items in data.items():
        pretty = section.capitalize()
        lines.append(f"- {pretty}: {', '.join(items)}")
    text = "\n".join(lines)
    await context.bot.send_message(chat_id=chat_id, text=text)


@check_student
async def faqs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return
    items = load_json_data("faqs.json")
    if not isinstance(items, list) or not items:
        await context.bot.send_message(chat_id=chat_id, text="No FAQs available.")
        return
    lines = ["FAQs:\n"]
    for qa in items:
        q = qa.get("q", "Q")
        a = qa.get("a", "A")
        lines.append(f"Q: {q}\nA: {a}\n")
    text = "\n".join(lines)
    await context.bot.send_message(chat_id=chat_id, text=text)


@check_student
async def deadlines(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return
    items = load_json_data("deadlines.json")
    if not isinstance(items, list) or not items:
        await context.bot.send_message(chat_id=chat_id, text="No deadlines available.")
        return
    lines = ["Upcoming Deadlines:\n"]
    for d in items:
        name = d.get("name", "Task")
        date = d.get("date", "TBD")
        details = d.get("details", "")
        detail_str = f" — {details}" if details else ""
        lines.append(f"- {date}: {name}{detail_str}")
    text = "\n".join(lines)
    await context.bot.send_message(chat_id=chat_id, text=text)


# --- News Scraping Handlers ---


@check_student
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get personalized tech news based on student's field of study."""
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return

    try:
        # Get student's field from user data (set by @check_student decorator)
        student_info = context.user_data.get("student_info", {})
        student_field = student_info.get("field", "")

        scraper = get_news_scraper()

        if student_field:
            field_emoji = scraper._get_field_emoji(student_field)
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"{field_emoji} Fetching personalized news for {student_field}...",
            )

            # Get personalized news based on student's field
            personalized_result = await scraper.get_personalized_news(
                student_field, limit=5
            )

            if personalized_result.get("success"):
                message = await scraper.format_news_for_telegram(personalized_result)
            else:
                # Fallback to field-specific content
                fallback_result = await scraper.get_fallback_news_for_field(
                    student_field
                )
                message = await scraper.format_news_for_telegram(fallback_result)
        else:
            # No field info, get general news
            await context.bot.send_message(
                chat_id=chat_id, text="📰 Fetching general tech news..."
            )
            fallback_result = await scraper.get_fallback_news()
            message = await scraper.format_news_for_telegram(fallback_result)
        # Send in chunks if too long
        MAX_LEN = 4000
        start = 0
        while start < len(message):
            chunk = message[start : start + MAX_LEN]
            await context.bot.send_message(chat_id=chat_id, text=chunk)
            start += MAX_LEN

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id, text=f"❌ Error fetching news: {str(e)}"
        )


async def hackernews(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get latest news from Hacker News."""
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return

    try:
        scraper = get_news_scraper()
        await context.bot.send_message(
            chat_id=chat_id, text="🔗 Fetching Hacker News..."
        )

        hn_result = await scraper.get_hacker_news(limit=5)

        if hn_result.get("success"):
            message = await scraper.format_news_for_telegram(hn_result)
        else:
            # Use fallback news if scraping fails
            print(
                f"Hacker News scraping failed, using fallback: {hn_result.get('error')}"
            )
            fallback_result = await scraper.get_fallback_news()
            message = await scraper.format_news_for_telegram(fallback_result)
            message = "🔗 Hacker News (Fallback Mode)\n\n" + message

        # Send in chunks if too long
        MAX_LEN = 4000
        start = 0
        while start < len(message):
            chunk = message[start : start + MAX_LEN]
            await context.bot.send_message(chat_id=chat_id, text=chunk)
            start += MAX_LEN

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id, text=f"❌ Error fetching Hacker News: {str(e)}"
        )


@check_student
async def technews(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get personalized tech news from various sources based on student's field."""
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return

    # Get student's field from user data
    student_info = context.user_data.get("student_info", {})
    student_field = student_info.get("field", "")

    # Get source from command arguments if provided, otherwise use personalized approach
    source = None
    if context.args:
        source = context.args[0].lower()

    try:
        scraper = get_news_scraper()

        if source:
            # Specific source requested
            # Call get_available_sources and await if it returns an awaitable
            _avail = scraper.get_available_sources()
            available_sources = await _avail if inspect.isawaitable(_avail) else _avail

            if source not in available_sources:
                sources_list = ", ".join(available_sources.keys())
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Unknown source: {source}\nAvailable sources: {sources_list}",
                )
                return

            source_info = available_sources[source]
            await context.bot.send_message(
                chat_id=chat_id, text=f"🔗 Fetching {source_info['name']}..."
            )

            tech_result = await scraper.get_tech_news(source, limit=5)
            print(tech_result)

            if tech_result.get("success") and student_field:
                # Filter the content for the student's field
                raw_content = str(tech_result.get("content", ""))
                _filtered = scraper.filter_content_by_field(raw_content, student_field)
                filtered_content = (
                    await _filtered if inspect.isawaitable(_filtered) else _filtered
                )
                tech_result["content"] = filtered_content

            if tech_result.get("success"):
                # format_news_for_telegram may be async; await if it returns an awaitable
                _msg = scraper.format_news_for_telegram(tech_result)
                message = await _msg if inspect.isawaitable(_msg) else _msg
            else:
                # Use field-specific fallback if scraping fails
                print(
                    f"Tech news scraping failed for {source}, using field-specific fallback"
                )
                fallback_result = (
                    await scraper.get_fallback_news_for_field(student_field)
                    if student_field
                    else await scraper.get_fallback_news()
                )
                _msg = scraper.format_news_for_telegram(fallback_result)
                message = await _msg if inspect.isawaitable(_msg) else _msg
                message = f"🔗 {source_info['name']} (Fallback Mode)\n\n" + message
        else:
            # No specific source, get personalized news based on field
            if student_field:
                field_emoji = scraper._get_field_emoji(student_field)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"{field_emoji} Fetching personalized tech news for {student_field}...",
                )

                personalized_result = await scraper.get_personalized_news(
                    student_field, limit=5
                )
                message = await scraper.format_news_for_telegram(personalized_result)
            else:
                # No field info, get general news
                await context.bot.send_message(
                    chat_id=chat_id, text="📰 Fetching general tech news..."
                )
                fallback_result = await scraper.get_fallback_news()
                message = await scraper.format_news_for_telegram(fallback_result)

        # Send in chunks if too long
        MAX_LEN = 4000
        start = 0
        while start < len(message):
            chunk = message[start : start + MAX_LEN]
            await context.bot.send_message(chat_id=chat_id, text=chunk)
            start += MAX_LEN

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id, text=f"❌ Error fetching tech news: {str(e)}"
        )


async def news_sources(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List available news sources."""
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return

    try:
        scraper = get_news_scraper()
        sources = scraper.get_available_sources()

        message = "📰 Available News Sources:\n\n"
        for source_name, source_info in sources.items():
            message += f"🔗 {source_info['name']} ({source_name})\n"
            message += f"   {source_info['description']}\n\n"

        message += "Usage: /technews <source_name>\nExample: /technews techcrunch"

        await context.bot.send_message(chat_id=chat_id, text=message)

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id, text=f"❌ Error getting news sources: {str(e)}"
        )


@check_student
async def my_news_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show student's personalized news profile and preferences."""
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return

    try:
        # Get student's field from user data
        student_info = context.user_data.get("student_info", {})
        student_field = student_info.get("field", "")
        student_name = student_info.get("complete_name", "Student")

        scraper = get_news_scraper()

        if student_field:
            field_emoji = scraper._get_field_emoji(student_field)
            keywords = scraper.get_field_keywords(student_field)

            message = f"{field_emoji} Your Personalized News Profile\n\n"
            message += f"👤 Name: {student_name}\n"
            message += f"📚 Field: {student_field}\n\n"
            message += f"🔍 Your news is filtered for these topics:\n"

            # Group keywords for better display
            keyword_chunks = [keywords[i : i + 3] for i in range(0, len(keywords), 3)]
            for chunk in keyword_chunks:
                message += f"• {', '.join(chunk)}\n"

            message += f"\n💡 Commands for you:\n"
            message += f"• /news - Get {student_field} news\n"
            message += f"• /technews - Get filtered tech news\n"
            message += f"• /hackernews - Get Hacker News\n"
            message += f"• /news_sources - See all sources\n\n"
            message += f"📰 All news content is automatically filtered to show relevant {student_field} information!"

        else:
            message = "❌ No field information found. Please contact admin to update your profile."

        await context.bot.send_message(chat_id=chat_id, text=message)

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id, text=f"❌ Error getting news profile: {str(e)}"
        )
