# SpeedLoader Bot

[![Tests](https://github.com/Elmun-Technologies/speedloadbot/actions/workflows/tests.yml/badge.svg)](https://github.com/Elmun-Technologies/speedloadbot/actions/workflows/tests.yml)

A comprehensive Telegram bot for downloading videos from various platforms with advanced features including AI content analysis, trend detection, and user management.

## Features

### 🎯 Core Functionality
- **Multi-Platform Support**: Download videos from YouTube, Instagram, TikTok, and more
- **Smart Format Detection**: Automatically detect and convert video formats
- **Quality Options**: Multiple resolution options for downloads
- **Universal Downloader**: Fallback system for unsupported platforms

### 🤖 AI-Powered Features
- **Content Analysis**: AI-powered content analysis and categorization
- **Trend Detection**: Real-time trend analysis and recommendations
- **Smart Transcription**: Automatic video transcription with translation
- **Content Safety**: AI-based content filtering and safety checks

### 📊 User Management
- **Multi-Language Support**: Full internationalization support
- **Referral System**: Built-in referral and reward system
- **Balance System**: User balance and transaction management
- **Streak System**: Daily usage tracking and rewards

### 🛡️ Security & Moderation
- **Content Filtering**: Advanced content safety and moderation
- **Rate Limiting**: Protection against abuse and spam
- **Admin Controls**: Comprehensive admin dashboard and controls
- **User Verification**: Account verification and management

### 📈 Analytics & Monitoring
- **Real-time Analytics**: Live statistics and user activity tracking
- **Trend Analysis**: Content trend detection and analysis
- **Performance Monitoring**: System performance and health monitoring
- **User Insights**: Detailed user behavior analytics

## Tech Stack

### Backend
- **Python 3.11+** - Main programming language
- **FastAPI** - High-performance web framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage
- **Celery** - Task queue and background jobs

### Frontend (Admin Dashboard)
- **Built-in lightweight dashboard** — a self-contained admin panel (`dashboard/index.html`, no build step) served by the FastAPI app at `/` and `/dashboard`. Login with the admin credentials, view stats, manage users (block/unblock, credits), answer tickets, browse trends and payments.
- **Full Next.js + TypeScript + Tailwind CSS + ShadCN UI dashboard** — 🚧 planned (`api/` admin API is ready to consume)

### Bot Framework
- **Python-Telegram-Bot** - Telegram bot framework
- **Redis** - Session and cache management
- **Celery** - Background task processing

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **FFmpeg** - Video processing and conversion
- **Cloud Storage** - File storage and CDN

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis
- Docker & Docker Compose
- FFmpeg

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Elmun-Technologies/speedloadbot.git
   cd speedloadbot
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

5. **Start the bot:**
   ```bash
   python bot/main.py
   ```

6. **Start the API:**
   ```bash
   python api/main.py
   ```

7. **Open the admin dashboard** (served by the API, no build step):
   - Start the API (`python api/main.py`) and open `http://localhost:8000/` — or `/dashboard`
   - Log in with `ADMIN_USERNAME` / `ADMIN_PASSWORD` from your `.env`

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token

# Admin bot commands (comma-separated Telegram user IDs; empty = disabled)
ADMIN_IDS=

# Database & Redis
DATABASE_URL=postgresql://user:password@localhost:5432/speedload
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# AI Services (optional — Trend Radar AI research & Whisper transcription)
OPENAI_API_KEY=

# Admin API / Dashboard (⚠️ set strong values in production)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me
JWT_SECRET=change_me_to_a_long_random_string
ADMIN_CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# API Server
API_HOST=0.0.0.0
API_PORT=8000
```

See `.env.example` for the full annotated list.

### Database Setup

Tables are created automatically on the first bot start (`init_db()` runs in `bot/main.py`). To create them manually (e.g. before starting only the API):

```bash
python -c "import asyncio; from database.connection import init_db; asyncio.run(init_db())"
```

## Usage

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start individual services
docker-compose up api
docker-compose up bot
docker-compose up admin
```

### Bot Commands

- `/start` - Start the bot
- `/help` - Get help information
- `/download [url]` - Download a video
- `/balance` - Check your balance
- `/referral` - Get referral link
- `/trends` - View trending content

### Admin Commands

- `/admin` - Access admin panel
- `/stats` - View statistics
- `/broadcast` - Send broadcast message
- `/users` - Manage users
- `/tickets` - Handle support tickets

Admin replies to tickets (bot `/tickets` or the dashboard/API `POST /admin/tickets/{id}/reply`) are delivered to the user on Telegram via a queued Celery task.

## Testing

The project has a comprehensive test suite (unit, integration and end-to-end):

```bash
# install dev dependencies (includes the pinned production requirements)
pip install -r requirements-dev.txt

# run the full suite
python -m pytest tests/ -q
```

What is covered:

| Area | How |
|---|---|
| Bot flows (E2E) | Real application + real SQLite DB; only Telegram HTTP, yt-dlp and Celery are faked (`tests/test_e2e_bot.py`) |
| Celery worker tasks | `process_download` (success / mp3 / too-large / failure) and `notify_ticket_reply`, executed in-process with a fake bot (`tests/test_tasks.py`) |
| Database CRUD | Real SQLite via aiosqlite (`tests/test_database.py`) |
| Admin API | FastAPI TestClient + SQLite dependency override (`tests/test_api.py`) |
| Rate limiter | fakeredis, incl. callback queries and Redis outage (`tests/test_rate_limit.py`) |
| Scheduled jobs | Active/non-banned user selection against a real DB (`tests/test_jobs.py`) |
| Pure helpers | Platform detection, content filter, greetings, smart-cut (`tests/test_detector.py`, `tests/test_human_touch.py`, `tests/test_aicut.py`) |

The suite also runs automatically on every push/PR via GitHub Actions (`.github/workflows/tests.yml`).

## Development

### Code Structure

```
speedloader/
├── api/                    # FastAPI backend
│   ├── main.py            # API entry point
│   ├── routes.py          # API endpoints
│   └── middleware.py      # Middleware
├── bot/                   # Telegram bot
│   ├── main.py           # Bot entry point
│   ├── handlers/         # Command handlers
│   ├── keyboards/        # Inline keyboards
│   └── middlewares/      # Bot middlewares
├── dashboard/            # Admin dashboard (static index.html, served by the API)
├── downloader/           # Download functionality
│   ├── youtube.py        # YouTube downloader
│   ├── instagram.py      # Instagram downloader
│   └── universal.py      # Universal downloader
├── database/             # Database models and CRUD
├── utils/                # Utility functions
│   ├── safety.py         # Content safety
│   ├── trends.py         # Trend analysis
│   ├── aicut.py          # AI content analysis
│   └── translations.py   # Internationalization
├── tasks/                # Background tasks
└── config.py            # Configuration
```

### Adding New Features

1. **Create database models** in `database/models.py`
2. **Add API endpoints** in `api/routes.py`
3. **Implement bot handlers** in `bot/handlers/`
4. **Update admin dashboard** in `dashboard/index.html` (plain HTML/JS, no build step)
5. **Add translations** in `utils/translations.py`

### Testing

```bash
# Install dev dependencies (includes pytest)
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Run with coverage
python -m pytest --cov=.
```

## Deployment

### Production Setup

1. **Build and start all services (bot, celery worker, API, postgres, redis):**
   ```bash
   docker-compose up -d --build
   ```

3. **Monitor:**
   ```bash
   docker-compose logs -f
   ```

### Monitoring

- **Health checks**: `/health` endpoint
- **Metrics**: Prometheus integration
- **Logging**: Structured logging with rotation
- **Error tracking**: Sentry integration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Style

- Follow PEP 8 for Python code
- Use type hints
- Write docstrings for all functions
- Use meaningful variable names

### Testing Guidelines

- Write unit tests for all new features
- Test edge cases and error conditions
- Use fixtures for test data
- Mock external dependencies

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [Wiki](https://github.com/Elmun-Technologies/speedloadbot/wiki)
- **Issues**: [GitHub Issues](https://github.com/Elmun-Technologies/speedloadbot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Elmun-Technologies/speedloadbot/discussions)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Python-Telegram-Bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)