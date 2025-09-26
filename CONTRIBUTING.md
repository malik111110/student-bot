# Contributing to Student Bot

Thanks for your interest in contributing! This document outlines a simple workflow and code style guidelines to help maintain a healthy project.

## How to contribute

1. Fork the repository.
2. Create a topic branch from `main` for your change: `git checkout -b feat/your-feature`.
3. Make your changes and add tests where appropriate.
4. Run the test suite locally: `pytest -q`.
5. Commit with a descriptive message and push your branch to your fork.
6. Open a pull request describing the change and linking any relevant issues.

## Code style

- Follow the existing project layout and naming conventions.
- Use type hints where appropriate.
- Keep functions small and focused. Add unit tests for new behaviour.

## Testing

- Add unit tests under `tests/unit/` and integration tests under `tests/integration/`.
- When tests require external services (DB, APIs), prefer mocking or provide guidance for running the services locally.

## PR checklist

- [ ] The change includes tests (or a reasonable explanation why not).
- [ ] All tests pass locally.
- [ ] Code is linted and follows style conventions.
- [ ] Documentation updated where necessary (README or inline comments).

## Communication

- For larger changes, open an issue first to discuss the design.
- Keep PRs focused and small when possible.

Thank you for helping improve Student Bot!
