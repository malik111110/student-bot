FEATURES — Student Bot

This document lists the core and supporting features of Student Bot, why each feature matters for students and maintainers, and short examples or implementation notes.

1. REST API Endpoints (courses, news, professors, schedule, etc.)

Description
- Structured HTTP endpoints that return JSON for campus data: courses, professors, schedules, deadlines, and news.

Why it matters
- Programmatic access: other services (mobile apps, web frontends, automation scripts) can consume consistent data.
- Testability: endpoints have predictable inputs and outputs making unit/integration testing straightforward.

Implementation notes
- Located under `api/endpoints/` and wired in `api/router.py`.
- Use `core/data_loader.py` as the canonical source for local JSON-backed data.

2. Conversational Bot Handlers

Description
- Message handlers that parse incoming text, match intents, and respond with formatted messages.

Why it matters
- Natural interface: students prefer conversational access (chat, messaging platforms) for quick questions.
- Extensibility: handlers can integrate with messaging platforms (Telegram, Slack) or be used in local simulations.

Implementation notes
- Located in `bot/handlers.py` and executed via `bot/runner.py`.

3. Local JSON Data Store and Loader

Description
- A collection of JSON files under `data/` that represent courses, schedules, professors, FAQs, and resources. `core/data_loader.py` loads and normalizes this data.

Why it matters
- Simple and portable: no DB required for local development or small deployments.
- Editable fixtures: easy to update data during testing or demos.

Implementation notes
- Consider migrating to a lightweight DB (SQLite, MongoDB) for larger deployments.

4. News Scraper

Description
- A small scraping utility (`core/news_scraper.py`) that fetches campus news items and returns structured articles.

Why it matters
- Keeps students informed with recent announcements and news, centralizing information sources.
- Useful for integrating alerts into the bot or email digests.

Implementation notes
- Use cached fixtures for tests to avoid flaky network dependencies. Implement retry/backoff for production.

5. Basic LLM Integration

Description
- `core/llm.py` provides helper functions to call LLM APIs or local models for richer conversational experiences or summarization.

Why it matters
- Enables paraphrasing, summarization of long announcements, or intelligent Q&A over static data.
- Helps provide more natural, context-aware replies.

Implementation notes
- Keep LLM usage behind a thin adapter to allow swapping providers and mocking during tests.

6. Text-to-Speech (TTS) Helpers

Description
- `core/tts.py` converts text responses to audio files for accessibility or voice-based interfaces.

Why it matters
- Accessibility: supports students who prefer audio or have visual impairments.
- Engagement: audio alerts or spoken summaries for important announcements.

Implementation notes
- Treat TTS providers' keys as secrets in environment variables. Cache generated audio where appropriate.

7. Message Formatter

Description
- `core/message_formatter.py` contains utilities to build consistent message outputs (markdown, text, or platform-specific payloads).

Why it matters
- Keeps conversational and API responses consistent and easy to style for multiple channels.

Implementation notes
- Add tests for formatting edge cases (long text, missing fields).

8. Simple DB Adapter

Description
- `core/db.py` contains a lightweight adapter for data persistence (optional in local mode).

Why it matters
- Provides a migration path from local JSON to a persistent store without rewriting business logic.

Implementation notes
- Prefer a small abstraction layer so switching to Mongo/MariaDB/Postgres is low-friction.

9. Scripts and Simulators

Description
- `scripts/` contains helper scripts like `simulate_bot.py`, `simulate_handlers.py`, and `ping_mongo.py` used for development and testing.

Why it matters
- Reduces manual testing time and provides reproducible scenarios for new contributors.

Implementation notes
- Keep scripts idempotent and document expected environment variables.

10. Tests (unit & integration)

Description
- Tests live under `tests/` and include both unit and integration tests.

Why it matters
- Ensures reliability and prevents regressions as new features are added.
- Encourages contributors to add tests for new behavior.

Implementation notes
- Use fixtures to avoid network calls; mock external APIs where appropriate.

11. Config & Environment Management

Description
- `core/config.py` centralizes configuration and environment variable handling.

Why it matters
- Makes the app portable between environments (dev, CI, production).

Implementation notes
- Consider using `pydantic` settings for type-checked configuration.

12. Developer Experience Enhancements

Description
- CONTRIBUTING.md, README, and simple scripts are present to onboard contributors quickly.

Why it matters
- Lowers the barrier for new contributors and helps maintain code quality.

Implementation notes
- Add CI to run tests on PRs and linting to enforce style.


Extras and suggested improvements

- Add a scheduled job worker (Celery, RQ) for scraping/news aggregation and long-running tasks.
- Add role-based access control (RBAC) for endpoints that manage sensitive data.
- Add analytics on queries to identify common student needs and prioritize features.
