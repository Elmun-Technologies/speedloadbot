from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
import uuid

from database.models import User, Download, Referral, DownloadStatus, Trend, TrendView
from utils.limits import evaluate_resets

async def get_user(session: AsyncSession, telegram_id: int):
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(session: AsyncSession, telegram_id: int, username: str, first_name: str, language_code: str = "uz", referred_by: int = None):
    ref_code = str(uuid.uuid4())[:12]
    # Make sure length of language is 2 max
    lang = language_code[:2] if language_code else "uz"
    if lang not in ["uz", "ru", "en"]:
        lang = "uz"
        
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        referral_code=ref_code,
        referred_by=referred_by,
        language=lang,
        action_count=0,
        total_creator_uses=0,
        streak_days=0,
        streak_last_date=None,
        credits=5,
        total_points=0,
        level=1,
        badges='[]'
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user_by_ref_code(session: AsyncSession, ref_code: str):
    stmt = select(User).where(User.referral_code == ref_code)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_referral(session: AsyncSession, referrer_id: int, referred_id: int):
    stmt = select(User).where(User.id == referrer_id)
    result = await session.execute(stmt)
    referrer = result.scalar_one_or_none()
    
    if referrer:
        referrer.referral_bonus += 2 
        referrer.total_referrals = (referrer.total_referrals or 0) + 1
        ref = Referral(referrer_id=referrer.id, referred_id=referred_id, coins_earned=2)
        session.add(ref)
        await session.commit()

async def update_user_language(session: AsyncSession, user_id: int, lang: str):
    stmt = update(User).where(User.id == user_id).values(language=lang)
    await session.execute(stmt)
    await session.commit()

async def update_user_profile(session: AsyncSession, user_id: int, **kwargs):
    stmt = update(User).where(User.id == user_id).values(**kwargs)
    await session.execute(stmt)
    await session.commit()

async def check_and_deduct_limit(session: AsyncSession, user: User) -> bool:
    evaluate_resets(user) # In-place mutation of User fields based on time
    
    if user.referral_bonus > 0:
        user.referral_bonus -= 1
        user.total_downloads += 1
        await session.commit()
        return True
    
    if user.downloads_week < 140 and user.downloads_6h > 0:
        user.downloads_6h -= 1
        user.downloads_week += 1
        user.total_downloads += 1
        await session.commit()
        return True
        
    await session.commit()
    return False

async def get_limits(session: AsyncSession, telegram_id: int):
    user = await get_user(session, telegram_id)
    if user:
        evaluate_resets(user)
        # return dict representing current state
        return {
            "downloads_6h": user.downloads_6h,
            "downloads_week": user.downloads_week,
            "referral_bonus": user.referral_bonus,
            "last_6h_reset": user.last_6h_reset,
            "last_week_reset": user.last_week_reset,
            "total_downloads": user.total_downloads
        }
    return None

async def create_download(session: AsyncSession, user_id: int, url: str, platform: str, quality: str, title: str = None, duration: int = None):
    dl = Download(
        user_id=user_id,
        url=url,
        platform=platform,
        quality=quality,
        title=title,
        duration=duration,
        status=DownloadStatus.pending
    )
    session.add(dl)
    await session.commit()
    await session.refresh(dl)
    return dl

async def update_download_status(session: AsyncSession, download_id: int, status: str, size: int = None):
    stmt = select(Download).where(Download.id == download_id)
    result = await session.execute(stmt)
    dl = result.scalar_one_or_none()
    if dl:
        dl.status = status
        if size is not None:
            dl.file_size = size
        await session.commit()

async def get_referral_stats(session: AsyncSession, user_id: int):
    stmt = select(Referral).where(Referral.referrer_id == user_id)
    result = await session.execute(stmt)
    referrals = result.scalars().all()
    count = len(referrals)
    earned = sum(r.coins_earned for r in referrals)
    return count, earned

async def update_user_engagement(session: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        now = datetime.utcnow()
        # Update action count
        user.action_count += 1
        
        # Streak logic
        last_action = user.last_action_date
        if last_action:
            # Normalize to dates for comparison
            now_date = now.date()
            last_date = last_action.date()
            diff = (now_date - last_date).days
            
            if diff == 1:
                user.streak += 1
            elif diff > 1:
                user.streak = 1
            # if diff == 0, keep same streak
        else:
            user.streak = 1
            
        user.last_action_date = now
        user.last_active = now
        await session.commit()
        return user
    return None

async def increment_creator_uses(session: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        user.total_creator_uses += 1
        await session.commit()
        return user
    return None

async def get_top_users_by_downloads(session: AsyncSession, limit: int = 10):
    # Weekly downloads leaderboard
    stmt = select(User).order_by(User.weekly_downloads.desc()).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

async def add_credits(session: AsyncSession, user_id: int, amount: int):
    stmt = select(User).where(User.telegram_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        user.credits += amount
        # Sync with creator_credits if used by other parts of the bot
        user.creator_credits = (user.creator_credits or 0) + amount
        await session.commit()
        return user
    return None

# === TREND RADAR CRUD ===

async def get_active_trends(session: AsyncSession, week: str = None, lang: str = 'uz'):
    if week:
        stmt = select(Trend).where(Trend.week_number == week, Trend.is_active == True, Trend.lang == lang).order_by(Trend.growth_percent.desc())
    else:
        stmt = select(Trend).where(Trend.is_active == True, Trend.lang == lang).order_by(Trend.growth_percent.desc()).limit(5)
    
    result = await session.execute(stmt)
    return result.scalars().all()

async def add_trend(session: AsyncSession, trend_data: dict):
    trend = Trend(**trend_data)
    session.add(trend)
    await session.commit()
    return trend

async def deactivate_old_trends(session: AsyncSession, current_week: str):
    stmt = update(Trend).where(Trend.week_number != current_week).values(is_active=False)
    await session.execute(stmt)
    await session.commit()

async def log_trend_view(session: AsyncSession, user_id: int, trend_id: int = None):
    view = TrendView(user_id=user_id, trend_id=trend_id)
    session.add(view)
    await session.commit()
    return view

async def get_active_users_for_notification(session: AsyncSession, days: int = 7):
    # Get users active in the last X days
    threshold = datetime.utcnow() - timedelta(days=days)
    stmt = select(User).where(User.last_active >= threshold)
    result = await session.execute(stmt)
    return result.scalars().all()

