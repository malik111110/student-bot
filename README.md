# Student Bot

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-pytest-orange.svg)](#testing)

A lightweight student assistant bot that exposes an API and a conversational bot interface to fetch course information, schedules, professors, news, and other student resources.

This repository implements a small Python-based bot and API server for students. It includes modules for data loading, news scraping, text-to-speech (TTS), basic LLM wrapping, and bot handlers.

## Motivation

Last year I served as the student representative for the graduating class of Computer Science. During that time I saw the same problems over and over: students confused about schedules, misinformed about deadlines, and overwhelmed by fragmented sources of information. As engineers we don't accept problems as immovable — we observe, identify, design, and build better solutions.

This bot is my practical response: a lightweight, pragmatic tool that brings trusted campus information together and makes it easy to access through an API or conversational interface. It's built to reduce friction for students, cut down misinformation, and provide a dependable single source of truth — all with extensibility and real-world use in mind.

If you're curious or want to help, the rest of this repository shows how the pieces fit together and how you can extend it to suit your own campus needs.

## Table of contents

- About
- Features
- Repository structure
- Installation
- Configuration
- Running the server and bot
- Tests
- Development notes
- Roadmap & contributions
- License

## About

The Student Bot provides quick access to campus-related information programmatically (via REST endpoints) and interactively (bot handlers). The project is structured to be simple to run locally and easy to extend.

## Features

- REST API endpoints for courses, news, professors, schedule, and AI utilities (see `api/endpoints`).
- Bot handlers to simulate or run an interactive assistant (see `bot/`).
- Local JSON-based dataset loader (see `data/` and `core/data_loader.py`).
- Simple news scraper (`core/news_scraper.py`) used by the news endpoints and tests.
- TTS helper and basic LLM wrapper under `core/` for experiments.

## Repository structure

Important files and folders:

- `main.py` — application entrypoint.
- `api/` — FastAPI router and endpoint implementations.
- `bot/` — bot handlers and runner used to process messages and simulate conversations.
- `core/` — core utilities: `config.py`, `data_loader.py`, `news_scraper.py`, `tts.py`, `llm.py`, `db.py`, `message_formatter.py`.
- `data/` — JSON test datasets (courses, schedule, professors, etc.).
- `tests/` — unit and integration tests. Run with `pytest`.
- `requirements.txt` — Python dependencies.

## Installation

Prerequisites:

- Python 3.11+ (project tested with Python 3.13 bytecode in this repo — use 3.11+).
- Optional: virtualenv or pyenv to manage Python versions.

Steps:

1. Clone the repo and enter the project directory.

2. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

If you need to add new packages, update `requirements.txt` and re-install.

## Configuration

The project reads configuration from `core/config.py`. Optional environment variables can be used to override values. Typical configuration keys include API host/port, database connection strings, and third-party API keys for LLM/TTS services.

Create an `.env` file in the project root (not committed) to set secret keys and environment-specific settings. Example:

```env
# Example .env
API_HOST=127.0.0.1
API_PORT=8000
MONGO_URI=mongodb://localhost:27017
OPENAI_API_KEY=your_openai_key_here
```

Make sure `.env` is ignored in `.gitignore` (this repo already excludes `.env`).

## Running the server and bot

Run the API server (the project uses a simple `main.py` entrypoint):

```bash
# activate environment
source .venv/bin/activate

python main.py
```

This will start the FastAPI app at the configured host/port (defaults are inside `core/config.py`).

Simulate the bot or run handlers:

```bash
python bot/runner.py
```

There are helper scripts in `scripts/` to exercise pieces of the project, e.g., `scripts/simulate_bot.py` and `scripts/ping_mongo.py`.

## Testing

Run the test suite using pytest:

```bash
pytest -q
```

The repository includes unit tests and integration tests under `tests/`. If tests rely on external services (like a local MongoDB), either mock them or run the service locally.

## Development notes

- Data: The `data/` folder contains JSON files used by `core/data_loader.py` for quick local development. Replace or augment them when needed.
- News scraper: `core/news_scraper.py` contains the scraping logic that feeds `/api/news` endpoints and related handlers. Use offline fixtures for tests to avoid flaky network calls.
- LLM & TTS: `core/llm.py` and `core/tts.py` provide thin wrappers for experimenting with AI models and text-to-speech; credentials should live in environment variables.
- API: `api/router.py` wires FastAPI endpoints located in `api/endpoints/`.

Edge cases to consider:

- Missing or malformed JSON data in `data/`.
- Network failures when calling external APIs (retry/backoff recommended).
- Long-running scraping tasks — consider background workers or scheduling.

## Adding features

To add a new endpoint:

1. Create a new module in `api/endpoints/` (e.g., `feedback.py`) and implement your route(s) using FastAPI.
2. Import and include the new router in `api/router.py`.
3. Add unit tests under `tests/unit/` and integration tests under `tests/integration/` as appropriate.

## Roadmap & contributions

Planned improvements:

- Add CI (GitHub Actions) with pytest and linting.
- Add type checking (mypy) and stricter lint rules.
- Dockerfile and compose file to run the API with a local MongoDB for integration tests.
- Better authentication for sensitive endpoints, plus rate-limiting for scraping.

Contributing:

1. Fork the repository.
2. Create a topic branch for your change.
3. Open a pull request describing your changes.

Please follow existing code style and add tests for new behavior.

## License

This project does not currently include a LICENSE file. Add one (for example MIT or Apache-2.0) to make licensing explicit before distributing.
