# SpeedLoader Bot

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

### Frontend
- **Next.js** - React framework for admin dashboard
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **ShadCN UI** - Component library

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

7. **Start the admin dashboard:**
   ```bash
   ./admin-dev.sh
   ```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/speedloader
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Storage
STORAGE_PATH=./downloads
MAX_FILE_SIZE=500MB

# AI Services
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_claude_key
```

### Database Setup

1. **Initialize database:**
   ```bash
   python -c "from database.connection import init_db; init_db()"
   ```

2. **Run migrations:**
   ```bash
   python migrate_trends.py
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
├── dashboard/            # Admin dashboard (Next.js)
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
4. **Update admin dashboard** in `dashboard/src/`
5. **Add translations** in `utils/translations.py`

### Testing

```bash
# Run tests
python -m pytest

# Run specific test
python -m pytest tests/test_downloader.py

# Run with coverage
python -m pytest --cov=.
```

## Deployment

### Production Setup

1. **Build Docker images:**
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```

2. **Deploy:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
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