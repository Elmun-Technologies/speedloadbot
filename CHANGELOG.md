# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup with comprehensive bot functionality
- Multi-platform video downloader (YouTube, Instagram, TikTok)
- AI-powered content analysis and trend detection
- Admin dashboard with user management and analytics
- Telegram bot with advanced features and moderation
- Database models for users, downloads, trends, and analytics
- Docker containerization for easy deployment
- Comprehensive API with FastAPI
- Multi-language support and internationalization
- Content safety and moderation system
- Referral and reward system
- User balance and transaction management
- Background task processing with Celery
- File size management and optimization
- Video processing and conversion with FFmpeg
- Real-time statistics and monitoring
- Trend analysis and recommendations
- User verification and account management
- Broadcast messaging system
- Support ticket system
- Daily streak tracking and rewards
- Smart content filtering and safety checks
- Automatic video transcription and translation
- Advanced rate limiting and abuse prevention
- Comprehensive logging and error handling
- Health checks and system monitoring
- Integration tests: CRUD layer (SQLite), admin API (TestClient + SQLite), rate limiter (fakeredis), conversation wiring
- `build_application()` factory in `bot/main.py` — builds the PTB application with an injectable bot instance (used by tests, real token used in production)
- End-to-end bot flow tests (`tests/test_e2e_bot.py`): full chain /start → language → interests → occupation → YouTube link → quality selection → database record + Celery dispatch, with only the outer boundaries faked (Telegram HTTP via a fake bot, yt-dlp extraction, Celery `.delay`)
- `tests/conftest.py` — points `DATABASE_URL` at a temp SQLite database before any project import, so integration tests share one isolated DB
- Rate-limiter tests for callback queries (unlimited) and Redis outage (fails open)
- Built-in admin dashboard (`dashboard/index.html`): a self-contained panel (no build step) served by the API at `/` and `/dashboard` — login, stats, user management (block/unblock, credits), ticket replies, trends and payments
- GitHub Actions CI workflow (`.github/workflows/tests.yml`) running the full test suite on every push/PR
- End-to-end edge-case tests: banned user is blocked, unsupported link gets an error reply, plain text is ignored silently
- Graceful-degradation test for the optional whisper transcriber
- Admin ticket replies now reach the user on Telegram: `POST /admin/tickets/{id}/reply` enqueues a `notify_ticket_reply` Celery task (executed by the worker, retried on failure, HTML-escaped); added the `ticket_reply_admin` translation key (uz/ru/en)
- `GET /admin/tickets` is now paginated (`page`/`limit` params) and returns the `total` count
- Tests for the worker tasks (`tests/test_tasks.py`: notification content, HTML escaping, user language) and for the whisper transcription formatting (fake model — no torch needed)
- Test coverage for the previously untested components: the Celery worker's `process_download` task end-to-end — success / mp3 / too-large / failure paths with a real SQLite DB and a fake bot (`tests/test_tasks.py`); scheduled jobs (`tests/test_jobs.py`); platform detection (`tests/test_detector.py`); human-touch helpers (`tests/test_human_touch.py`); the smart-cut shorts tool with mocked ffmpeg (`tests/test_aicut.py`)
- `ADMIN_IDS` is now read from the environment (comma-separated Telegram user IDs) instead of a hardcoded list in `bot/handlers/trends.py`; admin-only bot commands stay disabled until it is configured
- README: CI badge + a Testing section (how to run the suite, what is covered)

### Changed
- `requirements.txt` is now fully pinned to the tested environment (reproducible installs); `requirements-dev.txt` pinned as well
- `GET /health` now performs a real database probe (`{"status": ..., "database": ...}`) instead of returning a hardcoded constant
- README environment-variables block now matches `.env.example` (added `CELERY_*`, `JWT_SECRET`, `ADMIN_*`; removed unused `STORAGE_PATH` / `MAX_FILE_SIZE` / `ANTHROPIC_API_KEY`)
- CONTRIBUTING.md Testing section rewritten to describe the real test suite (it previously documented a non-existent `tests/unit|integration|fixtures` layout)

### Deprecated
- N/A

### Removed
- Dead dependencies removed from `requirements.txt`: `Pillow`, `mutagen`, `hachoir`, `hijri-converter`, `psycopg2-binary` (not imported anywhere in the codebase; shrinks the Docker image)
- `migrate_trends.py` — raw-SQL migration fully redundant with `init_db()` (`Base.metadata.create_all` covers both `trends` and `trend_views`)

### Fixed
- Fixed syntax error in `bot/handlers/account.py` (stray markdown fence) that prevented the bot from starting
- Added missing `detect_video_type` / `get_random_reaction` helpers in `utils/human_touch.py` (broken imports in the download handler)
- Download flow now actually sends the video info card with quality buttons (it was built but never sent — no download could ever start)
- Fixed `/language` callback: undefined `texts` variable and wrong user id field
- Fixed `/balance` handler (referenced non-existent `get_user_stats` and `coins` field) and wired it to the `/balance` command
- Fixed referral link and referral stats lookup in the Creator "buy credits" screen
- Fixed `datetime` column defaults in `database/models.py` (were frozen at import time instead of per-row)
- Removed broken `update_user_engagement` from `database/crud.py` (referenced non-existent model fields)
- Added missing translation keys (`language_updated`, `what_to_download`) for uz/ru/en
- Registered the Redis-backed rate-limit middleware (was never attached to the bot)
- Admin API: real statistics instead of hardcoded mock values; user search also matches username
- Replaced blocking yt-dlp calls in async handlers with `asyncio.to_thread`
- Removed committed `__pycache__` / `.DS_Store` artifacts; added `.DS_Store` to `.gitignore`
- Added `.dockerignore`; removed duplicate FFmpeg install in `Dockerfile`; added `api` service to `docker-compose.yml`
- Added smoke/unit tests (`tests/`) and `requirements-dev.txt`
- Gamification points for downloads are now awarded when a download actually starts (quality selected), not when a link is sent
- Banned users are now excluded from broadcasts and scheduled jobs
- Broadcast/job send rate reduced to stay safely under Telegram's flood limits
- Made `BigInteger` primary keys SQLite-compatible (`with_variant`) so the models work across databases
- **Critical: fixed `NameError` in `bot/main.py` — the handler was referenced as `handle_personalized_trend` but the function is named `handle_trend_personalized`; the bot crashed at startup (found by the new end-to-end test)**
- Rate limiting now applies to messages only — callback-query button taps stay unlimited, so multi-step flows like onboarding (4 taps) are no longer blocked by the 3/min limit
- Banned users are now blocked in the bot itself (`/start` and link messages get a "blocked" notice) — previously they were only excluded from broadcasts/jobs and could keep using the bot
- `utils/transcriber.py` no longer crashes at import when whisper/torch is not installed — it degrades to a friendly error message
- Added the missing `banned` translation key (uz/ru/en)
- Replaced the broken `dashboard` git submodule entry (no `.gitmodules` mapping — clones got an empty directory) with the real tracked `dashboard/index.html`
- `tasks/download_task.py`: `process_download` no longer leaks the Telegram bot session and the DB engine — both are closed in a `finally`, including the early-return too-large path
- `utils/aicut.py`: docstring no longer claims "AI" — it is a deterministic FFmpeg-based cutter (fixed-position highlights)
- README setup: the `init_db()` one-liner now actually awaits the coroutine (`asyncio.run(...)`); removed the redundant migration step

### Security
- Removed hardcoded default secrets (`ADMIN_PASSWORD`, `JWT_SECRET`) from `config.py` — the admin API refuses to issue tokens until they are set via environment variables
- Added `POST /admin/login` endpoint issuing short-lived (12h) admin JWTs with constant-time credential comparison
- Restricted admin API CORS to configured origins (was `*` together with credentials)

## [1.0.0] - 2024-03-20

### Added
- Initial release of SpeedLoader Bot
- Complete feature set for video downloading and management
- Production-ready deployment configuration
- Comprehensive documentation and setup guides
- Testing framework and CI/CD ready structure

## Future Releases

### Planned Features
- **Enhanced AI Features**
  - Advanced content recommendation engine
  - Smart video editing and enhancement
  - AI-powered video summarization
  - Content quality assessment

- **Platform Expansion**
  - Support for additional video platforms
  - Social media integration
  - Cloud storage integration
  - CDN optimization

- **User Experience Improvements**
  - Mobile app development
  - Enhanced UI/UX design
  - Voice command integration
  - Dark mode and theme customization

- **Advanced Analytics**
  - Predictive analytics for content trends
  - User behavior analysis
  - Performance optimization recommendations
  - A/B testing framework

- **Enterprise Features**
  - Team collaboration tools
  - Advanced permission management
  - Bulk operations and batch processing
  - Enterprise-grade security features

- **Integration Ecosystem**
  - Third-party API integrations
  - Plugin system for custom functionality
  - Webhook support for external services
  - Marketplace for extensions

## Migration Notes

### From Previous Versions
- N/A (Initial release)

### Breaking Changes
- N/A

### Upgrade Instructions
- N/A

## Contributing to the Changelog

When contributing to this project, please update this changelog for any user-facing changes:

1. **Added**: New features or functionality
2. **Changed**: Modifications to existing features
3. **Deprecated**: Features that will be removed in future versions
4. **Removed**: Features that have been removed
5. **Fixed**: Bug fixes and issue resolutions
6. **Security**: Security-related changes

### Changelog Format

```markdown
## [Version] - YYYY-MM-DD

### Added
- New feature description

### Changed
- Modified feature description

### Fixed
- Bug fix description
```

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH**
- **MAJOR**: Breaking changes that require user action
- **MINOR**: New features that are backward compatible
- **PATCH**: Bug fixes and minor improvements

## Release Process

1. **Feature Freeze**: Stop accepting new features 1 week before release
2. **Testing Phase**: Comprehensive testing of all features
3. **Documentation Update**: Update documentation and changelog
4. **Release Notes**: Prepare release notes and announcements
5. **Deployment**: Deploy to production environment
6. **Monitoring**: Monitor for issues and user feedback

## Support

For questions about this changelog or the project:
- [GitHub Issues](https://github.com/Elmun-Technologies/speedloadbot/issues)
- [GitHub Discussions](https://github.com/Elmun-Technologies/speedloadbot/discussions)
- [Documentation](https://github.com/Elmun-Technologies/speedloadbot/wiki)