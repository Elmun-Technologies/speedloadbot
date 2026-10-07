# Contributing to SpeedLoader Bot

Thank you for considering contributing to SpeedLoader Bot! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Feature Requests](#feature-requests)
- [Bug Reports](#bug-reports)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful in all interactions and follow professional standards of conduct.

## How to Contribute

There are many ways to contribute to SpeedLoader Bot:

- **Report bugs** - Help us identify and fix issues
- **Request features** - Suggest new features or improvements
- **Submit pull requests** - Implement fixes or new functionality
- **Improve documentation** - Help make our docs clearer and more comprehensive
- **Answer questions** - Help other users on discussions and issues

## Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- Docker & Docker Compose
- FFmpeg

### Local Development

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/speedloadbot.git
   cd speedloadbot
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

5. **Initialize the database:**
   ```bash
   python -c "from database.connection import init_db; init_db()"
   ```

6. **Run the application:**
   ```bash
   # Start the bot
   python bot/main.py
   
   # Start the API
   python api/main.py
   
   # Start the admin dashboard
   ./admin-dev.sh
   ```

## Code Style

### Python

We follow PEP 8 style guidelines with the following additional rules:

- **Line length**: Maximum 88 characters (using Black formatter)
- **Type hints**: All functions must have type hints
- **Docstrings**: All public functions and classes need docstrings
- **Imports**: Organize imports in the following order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports

**Example:**
```python
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserCreate, UserResponse


def create_user(user_data: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    """
    Create a new user in the database.
    
    Args:
        user_data: User creation data
        db: Database session dependency
        
    Returns:
        UserResponse: Created user data
        
    Raises:
        HTTPException: If user already exists
    """
    # Implementation here
    pass
```

### JavaScript/TypeScript

For the admin dashboard:

- **ESLint**: Use our ESLint configuration
- **Prettier**: Use our Prettier configuration
- **TypeScript**: Strict mode enabled
- **Naming**: Use camelCase for variables and functions

### Git Commit Messages

Use clear, descriptive commit messages:

```
feat: add user authentication system

- Implement JWT token-based authentication
- Add login/logout endpoints
- Include middleware for token validation

Closes #123
```

**Commit message format:**
- Use present tense ("add" not "added")
- Use imperative mood ("move" not "moves")
- Limit the first line to 72 characters
- Reference issues and pull requests liberally after the first line

## Testing

The project has a comprehensive test suite (100+ tests: unit, integration and
end-to-end). Tests run against a real SQLite database — PostgreSQL, Redis,
Telegram, yt-dlp and Celery are faked at the outer boundaries only.

### Test Structure

```
tests/
├── conftest.py            # session-wide temp SQLite DATABASE_URL (set before imports)
├── test_smoke.py          # all modules import; optional deps degrade gracefully
├── test_translations.py   # translation key parity across uz/ru/en
├── test_utils.py          # config & misc utilities
├── test_config.py         # configuration handling
├── test_database.py       # CRUD layer (real SQLite)
├── test_api.py            # admin API (TestClient + SQLite dependency override)
├── test_rate_limit.py     # rate limiter (fakeredis)
├── test_conversations.py  # conversation/handler wiring
├── test_e2e_bot.py        # full bot flows E2E (onboarding, download, bans, edge cases)
├── test_tasks.py          # Celery worker tasks (process_download, notify_ticket_reply)
├── test_jobs.py           # scheduled jobs (active/non-banned user selection)
├── test_detector.py       # platform detection
├── test_human_touch.py    # content filter, greetings, video-type detection
└── test_aicut.py          # smart-cut shorts tool (ffmpeg mocked)
```

### Writing Tests

1. **Prefer real components**: use the real SQLite DB (aiosqlite) and fake only
   the outer boundaries (Telegram HTTP, yt-dlp, Celery, ffmpeg).
2. **One concern per test**: name tests after the behavior they verify.
3. **No network**: tests must run fully offline (CI has no Telegram/Redis/PG).

**Example test (API endpoint with a test database):**
```python
def test_stats_returns_real_data(client):
    token = login(client)
    r = client.get("/admin/stats", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["totalUsers"] == 2  # seeded by the `client` fixture
```

### Running Tests

```bash
# install dev dependencies (includes the pinned production requirements)
pip install -r requirements-dev.txt

# run the full suite
python -m pytest tests/ -q

# run a specific test file
python -m pytest tests/test_api.py -q

# run tests matching a pattern
python -m pytest tests/ -k "download" -q

# verbose output
python -m pytest tests/ -v
```

The suite also runs automatically on every push/PR via GitHub Actions
(`.github/workflows/tests.yml`).

## Submitting Changes

### Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and ensure tests pass:
   ```bash
   pytest
   ```

3. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

4. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** on GitHub with:
   - Clear title describing the change
   - Detailed description of what was changed
   - Reference to related issues (e.g., "Closes #123")
   - Screenshots for UI changes (if applicable)

### Pull Request Guidelines

- **Small PRs**: Keep changes focused and small when possible
- **Tests**: Include tests for new functionality
- **Documentation**: Update documentation for new features
- **Changelog**: Add entries to CHANGELOG.md for user-facing changes
- **Review**: Be responsive to code review feedback

## Feature Requests

To request a new feature:

1. **Check existing issues**: Make sure the feature hasn't already been requested
2. **Create an issue** with the "feature request" label
3. **Provide details**:
   - Clear description of the feature
   - Use case and why it's needed
   - Any design considerations
   - Examples of similar features in other projects

## Bug Reports

To report a bug:

1. **Check existing issues**: Make sure the bug hasn't already been reported
2. **Create an issue** with the "bug" label
3. **Provide detailed information**:
   - Clear description of the bug
   - Steps to reproduce
   - Expected behavior vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Error messages and stack traces
   - Screenshots (if applicable)

**Bug report template:**
```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment info:**
- OS: [e.g. macOS, Windows, Linux]
- Python version: [e.g. 3.11.5]
- SpeedLoader version: [e.g. latest from main]

**Additional context**
Add any other context about the problem here.
```

## Development Workflow

### For Maintainers

1. **Review PRs**: Check for code quality, tests, and documentation
2. **Test locally**: Ensure changes work as expected
3. **Merge strategy**: Use squash merge for small changes, rebase for larger features
4. **Release process**: Follow semantic versioning and update changelog

### For Contributors

1. **Communication**: Use GitHub discussions for questions
2. **Feedback**: Be open to code review feedback
3. **Follow-up**: Address review comments promptly
4. **Learning**: Use the opportunity to learn and improve

## Questions?

If you have questions about contributing, please:

- Check the [GitHub Discussions](https://github.com/Elmun-Technologies/speedloadbot/discussions)
- Open an issue with the "question" label
- Join our community chat (if available)

Thank you for contributing to SpeedLoader Bot! 🚀