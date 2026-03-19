import asyncio
import json
from datetime import datetime
from database.connection import AsyncSessionLocal
from database.crud import get_user, update_user_profile, add_credits
from utils.streak_system import (
    POINTS_CONFIG, get_level, check_and_award_badges, 
    update_streak_logic, STREAK_MESSAGES, get_level_up_msg, BADGES
)

async def process_user_action(user_id, action_type, bot, lang='uz'):
    """
    High-level wrapper called after user actions.
    Coordinates streaks, points, levels, and badges.
    """
    async with AsyncSessionLocal() as session:
        db_user = await get_user(session, user_id)
        if not db_user:
            return

        # Convert SQLAlchemy object to dict for utility functions
        user_data = {
            'name': db_user.first_name,
            'telegram_id': db_user.telegram_id,
            'created_at': db_user.created_at,
            'total_downloads': db_user.total_downloads,
            'daily_downloads': db_user.daily_downloads,
            'weekly_downloads': db_user.weekly_downloads,
            'total_creator_uses': db_user.total_creator_uses,
            'daily_creator_uses': db_user.daily_creator_uses,
            'total_referrals': db_user.total_referrals,
            'streak_days': db_user.streak_days,
            'streak_last_date': db_user.streak_last_date,
            'streak_longest': db_user.streak_longest,
            'total_points': db_user.total_points,
            'level': db_user.level,
            'badges': db_user.badges,
            'daily_reset_date': db_user.daily_reset_date,
            'weekly_reset_date': db_user.weekly_reset_date,
            'credits': db_user.credits
        }

        # 1. Update streak and daily/weekly counters
        user_data, streak_notifs = update_streak_logic(user_data)

        # 2. Update action counts
        if action_type == 'download':
            user_data['total_downloads'] = user_data.get('total_downloads', 0) + 1
            user_data['daily_downloads'] = user_data.get('daily_downloads', 0) + 1
            user_data['weekly_downloads'] = user_data.get('weekly_downloads', 0) + 1
        elif action_type == 'creator_use':
            user_data['total_creator_uses'] = user_data.get('total_creator_uses', 0) + 1
            user_data['daily_creator_uses'] = user_data.get('daily_creator_uses', 0) + 1

        # 3. Add points
        points_earned = POINTS_CONFIG.get(action_type, 0)
        
        # Check first-time actions
        if action_type == 'download' and user_data['total_downloads'] == 1:
            points_earned += POINTS_CONFIG.get('first_download', 0)
        elif action_type == 'creator_use' and user_data['total_creator_uses'] == 1:
            points_earned += POINTS_CONFIG.get('first_creator', 0)
            
        old_points = user_data.get('total_points', 0)
        user_data['total_points'] = old_points + points_earned
        
        # 4. Check Level Up
        old_level_data = get_level(old_points)
        new_level_data = get_level(user_data['total_points'])
        leveled_up = new_level_data['level'] > old_level_data['level']
        user_data['level'] = new_level_data['level']

        # 5. Check Badges
        new_badges, all_badges = check_and_award_badges(user_data)
        user_data['badges'] = json.dumps(all_badges)

        # 6. Save updates to DB
        update_fields = {
            'streak_days': user_data['streak_days'],
            'streak_last_date': user_data['streak_last_date'],
            'streak_longest': user_data['streak_longest'],
            'total_points': user_data['total_points'],
            'level': user_data['level'],
            'badges': user_data['badges'],
            'daily_downloads': user_data['daily_downloads'],
            'daily_creator_uses': user_data['daily_creator_uses'],
            'daily_reset_date': user_data['daily_reset_date'],
            'weekly_downloads': user_data['weekly_downloads'],
            'weekly_reset_date': user_data['weekly_reset_date'],
            'total_downloads': user_data['total_downloads'],
            'total_creator_uses': user_data['total_creator_uses'],
            'last_active': user_data['last_active']
        }
        await update_user_profile(session, db_user.id, **update_fields)

        # 7. Handle Notifications
        # Level Up
        if leveled_up:
            bonus = new_level_data['credits_bonus']
            if bonus > 0:
                await add_credits(session, user_id, bonus)
            
            msg = f"🎉 TABRIKLAYMIZ, {user_data['name']}!" \
                  f"\n\n⬆️ Yangi daraja: {new_level_data['name'] if lang=='uz' else new_level_data['name_ru']}" \
                  f"\n\n🎁 Bonus: +{bonus} kredit hisobingizga qo'shildi!" \
                  f"\n\n{get_level_up_msg(user_data['level'], lang)}" \
                  f"\n\n💪 Davom eting — keyingi daraja sizni kutmoqda!"
            await bot.send_message(user_id, msg)

        # Badges
        for b_key in new_badges:
            badge = BADGES[b_key]
            msg = f"🏅 YANGI NISHON OLDINGIZ!" \
                  f"\n\n{badge['emoji']} {badge['name'] if lang=='uz' else b_key}" \
                  f"\n📝 {badge['desc'] if lang=='uz' else 'Вы заработали новый значок!'}" \
                  f"\n\nZo'r, {user_data['name']}! Davom eting! 🚀"
            await bot.send_message(user_id, msg)

        # Streaks
        for notif in streak_notifs:
            msg_temp = STREAK_MESSAGES.get(lang, STREAK_MESSAGES['uz']).get(notif)
            if msg_temp:
                msg = msg_temp.format(name=user_data['name'], streak=user_data['streak_days'])
                await asyncio.sleep(1)
                await bot.send_message(user_id, msg)
