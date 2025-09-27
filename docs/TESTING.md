# Testing Guide

This document provides comprehensive information about testing the InfoSec Bot project.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests
│   ├── test_config.py       # Configuration testing
│   ├── test_data_loader.py  # Data loading utilities
│   ├── test_bot_handlers.py # Bot command handlers
│   └── test_llm.py         # LLM integration
├── integration/             # Integration tests
│   ├── test_api_endpoints.py # API endpoint testing
│   ├── test_database.py     # Database operations
│   └── test_telegram_bot.py # Bot integration
├── performance/             # Performance tests
│   └── test_load.py        # Load and stress testing
└── security/               # Security tests
    └── test_security.py    # Security vulnerability testing
```

## Running Tests

### All Tests
```bash
pytest
```

### Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Security tests only
pytest tests/security/ -m security

# Performance tests only
pytest tests/performance/ -m performance

# Exclude slow tests
pytest -m "not slow"
```

### With Coverage
```bash
# Generate coverage report
pytest --cov=core --cov=api --cov=bot --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Configuration

### Environment Variables
Create a `.env.test` file for test-specific configuration:

```bash
# Test environment
ENVIRONMENT=test
TELEGRAM_TOKEN=test_token
FIRECRAWL_API_KEY=test_key
ELEVEN_LAB_API_KEY=test_key
OPENROUTER_API_KEY=test_key

# Test database
MONGODB_URI=mongodb://localhost:27017/infosec_bot_test
SUPABASE_URL=https://test.supabase.co
SUPABASE_KEY=test_key

# Disable external services in tests
DISABLE_EXTERNAL_CALLS=true
```

### Pytest Configuration
The `pytest.ini` file contains:
- Coverage settings
- Test markers
- Warning filters
- Async test configuration

## Test Types

### Unit Tests
Test individual components in isolation:
- Configuration loading
- Data processing functions
- Bot command handlers
- LLM integration
- Utility functions

### Integration Tests
Test component interactions:
- API endpoints
- Database operations
- Bot-to-API communication
- External service integration

### Performance Tests
Test system performance:
- Response time benchmarks
- Concurrent request handling
- Memory usage monitoring
- Database query performance

### Security Tests
Test security vulnerabilities:
- SQL injection protection
- XSS prevention
- Command injection protection
- Authentication bypass attempts
- Input validation

## Mocking Strategy

### External Services
Mock external API calls:
```python
@patch('core.llm.openai_client')
def test_llm_response(mock_client):
    mock_client.chat.completions.create.return_value = mock_response
    # Test implementation
```

### Database Operations
Mock database calls:
```python
@patch('core.database.supabase')
def test_database_query(mock_supabase):
    mock_supabase.table.return_value.select.return_value = mock_data
    # Test implementation
```

### Telegram Bot
Mock bot interactions:
```python
@pytest.fixture
def mock_telegram_update():
    update = MagicMock()
    update.effective_user.id = 12345
    update.message.text = "test message"
    return update
```

## Test Data

### Fixtures
Common test data is defined in `conftest.py`:
- Sample student data
- Course information
- Professor details
- Schedule data

### Test Database
Use a separate test database:
- Isolated from production data
- Reset between test runs
- Seeded with test data

## Continuous Integration

### GitHub Actions
Tests run automatically on:
- Pull requests
- Pushes to main branch
- Scheduled runs (daily)

### Test Matrix
Tests run against:
- Python 3.11
- Multiple OS (Ubuntu, macOS, Windows)
- Different dependency versions

## Best Practices

### Writing Tests
1. **Descriptive Names**: Use clear, descriptive test names
2. **Single Responsibility**: Each test should test one thing
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Independent Tests**: Tests should not depend on each other
5. **Mock External Dependencies**: Don't rely on external services

### Test Coverage
- Aim for >90% code coverage
- Focus on critical business logic
- Test error conditions and edge cases
- Include both positive and negative test cases

### Performance Testing
- Set realistic performance benchmarks
- Test under various load conditions
- Monitor resource usage
- Test timeout handling

### Security Testing
- Test all input validation
- Verify authentication/authorization
- Check for common vulnerabilities
- Test error message disclosure

## Debugging Tests

### Running Single Tests
```bash
# Run specific test
pytest tests/unit/test_config.py::TestConfig::test_load_config

# Run with verbose output
pytest -v -s tests/unit/test_config.py

# Run with debugging
pytest --pdb tests/unit/test_config.py
```

### Test Debugging Tips
1. Use `pytest -s` to see print statements
2. Use `pytest --pdb` to drop into debugger on failure
3. Use `pytest -x` to stop on first failure
4. Use `pytest --lf` to run only last failed tests

## Test Maintenance

### Regular Tasks
- Update test data as application evolves
- Review and update mocks when APIs change
- Monitor test execution time
- Update security tests for new vulnerabilities
- Review coverage reports and add missing tests

### Refactoring Tests
- Extract common test utilities
- Update fixtures when data models change
- Consolidate similar test cases
- Remove obsolete tests

## Troubleshooting

### Common Issues
1. **Async Test Failures**: Ensure proper async/await usage
2. **Mock Issues**: Verify mock paths and return values
3. **Database Tests**: Check test database connectivity
4. **Flaky Tests**: Identify and fix non-deterministic behavior

### Getting Help
- Check test logs for detailed error messages
- Review similar test implementations
- Consult pytest documentation
- Ask team members for assistance