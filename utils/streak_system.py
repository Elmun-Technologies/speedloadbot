import json
import random
from datetime import datetime, date
from utils.translations import TEXTS

# === 1. POINTS SYSTEM ===

POINTS_CONFIG = {
    'download':         5,   # Every video download
    'creator_use':      10,  # Every creator tool use
    'referral':         50,  # Each friend invited
    'daily_login':      2,   # Just opening bot
    'trend_view':       3,   # Viewing Trend Radar
    'streak_7days':     25,  # 7-day streak bonus
    'streak_30days':    100, # 30-day streak bonus
    'streak_100days':   500, # 100-day streak bonus!
    'first_download':   20,  # First ever download
    'first_creator':    30,  # First creator tool use
}

# === 2. LEVELS SYSTEM ===

LEVELS = [
    {'level': 1,  'name': '🌱 Yangi Foydalanuvchi', 'name_ru': '🌱 Новичок',           'min_points': 0,     'credits_bonus': 0},
    {'level': 2,  'name': '⚡ Faol Foydalanuvchi',  'name_ru': '⚡ Активный',           'min_points': 100,   'credits_bonus': 5},
    {'level': 3,  'name': '🎯 Ijodkor',              'name_ru': '🎯 Творец',             'min_points': 300,   'credits_bonus': 10},
    {'level': 4,  'name': '🔥 Pro Foydalanuvchi',   'name_ru': '🔥 Про пользователь',   'min_points': 700,   'credits_bonus': 20},
    {'level': 5,  'name': '💎 Creator',              'name_ru': '💎 Криэйтор',           'min_points': 1500,  'credits_bonus': 35},
    {'level': 6,  'name': '🏆 Expert',               'name_ru': '🏆 Эксперт',            'min_points': 3000,  'credits_bonus': 50},
    {'level': 7,  'name': '🌟 Master Creator',       'name_ru': '🌟 Мастер Криэйтор',    'min_points': 6000,  'credits_bonus': 100},
    {'level': 8,  'name': '👑 Legend',               'name_ru': '👑 Легенда',            'min_points': 12000, 'credits_bonus': 200},
]

def get_level(points: int) -> dict:
    current = LEVELS[0]
    for lvl in LEVELS:
        if points >= lvl['min_points']:
            current = lvl
        else:
            break
    return current

def get_next_level(points: int) -> dict or None:
    current = get_level(points)
    current_idx = next(
        (i for i, l in enumerate(LEVELS) if l['level'] == current['level']),
        None
    )
    if current_idx is not None and current_idx + 1 < len(LEVELS):
        return LEVELS[current_idx + 1]
    return None

# === 3. BADGES SYSTEM ===

BADGES = {
    'first_blood':    {'emoji': '🩸', 'name': 'Birinchi yuklab olish',  'desc': 'Birinchi videoni yuklab oldingiz!'},
    'speed_demon':    {'emoji': '⚡', 'name': 'Tez Ijodkor',            'desc': '10 ta video bir kunda!'},
    'week_warrior':   {'emoji': '🗓', 'name': 'Hafta Jangchisi',        'desc': '7 kun ketma-ket foydalandingiz!'},
    'month_master':   {'emoji': '📅', 'name': 'Oy Ustasi',              'desc': '30 kun ketma-ket streak!'},
    'creator_pro':    {'emoji': '🎨', 'name': 'Creator Pro',            'desc': 'Creator vositalarini 50 marta ishlatdingiz!'},
    'social_butterfly':{'emoji': '🦋','name': 'Ijtimoiy Kapalak',       'desc': '10 do\'st taklif qildingiz!'},
    'century_club':   {'emoji': '💯', 'name': 'Yuz Klubi',              'desc': '100 ta video yuklab oldingiz!'},
    'night_owl':      {'emoji': '🦉', 'name': 'Tungi Boyqush',          'desc': 'Tunda 10 marta foydalandingiz!'},
    'early_bird':     {'emoji': '🐦', 'name': 'Erta Turuvchi',          'desc': 'Ertalab 6-8 da 5 marta foydalandingiz!'},
    'trend_hunter':   {'emoji': '🔥', 'name': 'Trend Ovchi',            'desc': 'Trend Radarni 20 marta ko\'rdingiz!'},
    'loyal_fan':      {'emoji': '💙', 'name': 'Sodiq Foydalanuvchi',    'desc': '100 kun foydalanish!'},
    'legend':         {'emoji': '👑', 'name': 'Afsona',                 'desc': 'Level 8 ga yetdingiz — siz LEGEND!'},
}

def check_and_award_badges(user_data: dict) -> tuple:
    """Returns tuple of (newly earned badge keys, all earned badges)"""
    badges_str = user_data.get('badges', '[]')
    if not badges_str: badges_str = '[]'
    
    try:
        earned = json.loads(badges_str)
    except:
        earned = []
        
    new_badges = []

    level = user_data.get('level', 1)
    
    checks = {
        'first_blood':     user_data.get('total_downloads', 0) >= 1,
        'speed_demon':     user_data.get('daily_downloads', 0) >= 10,
        'week_warrior':    user_data.get('streak_days', 0) >= 7,
        'month_master':    user_data.get('streak_days', 0) >= 30,
        'creator_pro':     user_data.get('total_creator_uses', 0) >= 50,
        'social_butterfly':user_data.get('total_referrals', 0) >= 10,
        'century_club':    user_data.get('total_downloads', 0) >= 100,
        'loyal_fan':       user_data.get('streak_days', 0) >= 100,
        'legend':          level >= 8,
    }

    for badge_key, condition in checks.items():
        if condition and badge_key not in earned:
            earned.append(badge_key)
            new_badges.append(badge_key)

    return new_badges, earned

# === 4. STREAK LOGIC ===

def update_streak_logic(user_data: dict) -> tuple:
    """
    Core streak update logic. Returns (updated_user_data, notifications).
    Works on a dict representing the user.
    """
    today = date.today()
    notifications = []

    # === UPDATE DAILY RESET ===
    daily_reset = user_data.get('daily_reset_date')
    if isinstance(daily_reset, datetime): daily_reset = daily_reset.date()
    elif isinstance(daily_reset, str): daily_reset = date.fromisoformat(daily_reset)
    
    if daily_reset != today:
        user_data['daily_downloads'] = 0
        user_data['daily_creator_uses'] = 0
        user_data['daily_reset_date'] = today

    # === UPDATE WEEKLY RESET ===
    week_start = today.strftime('%Y-W%W')
    if user_data.get('weekly_reset_date') != week_start:
        user_data['weekly_downloads'] = 0
        user_data['weekly_reset_date'] = week_start

    # === STREAK LOGIC ===
    last_date = user_data.get('streak_last_date')
    if isinstance(last_date, datetime): last_date = last_date.date()
    elif isinstance(last_date, str): last_date = date.fromisoformat(last_date)
    
    streak = user_data.get('streak_days', 0)

    if last_date is None:
        # First time
        streak = 1
        notifications.append('new_streak')
    elif last_date == today:
        # Already active today — just continue
        pass
    elif (today - last_date).days == 1:
        # Consecutive day — increment streak!
        streak += 1

        # Streak milestone notifications
        if streak == 3:
            notifications.append('streak_3')
        elif streak == 7:
            notifications.append('streak_7')
            user_data['total_points'] = user_data.get('total_points', 0) + POINTS_CONFIG['streak_7days']
        elif streak == 14:
            notifications.append('streak_14')
        elif streak == 30:
            notifications.append('streak_30')
            user_data['total_points'] = user_data.get('total_points', 0) + POINTS_CONFIG['streak_30days']
        elif streak == 100:
            notifications.append('streak_100')
            user_data['total_points'] = user_data.get('total_points', 0) + POINTS_CONFIG['streak_100days']
        elif streak % 50 == 0:
            notifications.append(f'streak_{streak}')
    else:
        # Streak broken!
        if streak >= 7:
            notifications.append('streak_broken')
        streak = 1

    user_data['streak_days'] = streak
    user_data['streak_last_date'] = today
    user_data['last_active'] = datetime.utcnow() # Detailed timestamp for internal use

    # Update longest streak
    if streak > user_data.get('streak_longest', 0):
        user_data['streak_longest'] = streak

    return user_data, notifications

# === 5. PROFILE FORMATTING ===

def format_full_profile(user_data: dict, lang: str = 'uz') -> str:
    name = user_data.get('name', 'Foydalanuvchi')
    user_id = user_data.get('telegram_id', '')
    
    join_date = user_data.get('created_at', date.today())
    if isinstance(join_date, str):
        join_date = datetime.fromisoformat(join_date)
    
    downloads = user_data.get('total_downloads', 0)
    creator_uses = user_data.get('total_creator_uses', 0)
    referrals = user_data.get('total_referrals', 0)
    credits = user_data.get('credits', 0)
    streak = user_data.get('streak_days', 0)
    longest_streak = user_data.get('streak_longest', 0)
    points = user_data.get('total_points', 0)
    
    badges_raw = user_data.get('badges', '[]')
    if not badges_raw: badges_raw = '[]'
    try:
        badges_list = json.loads(badges_raw)
    except:
        badges_list = []

    current_level = get_level(points)
    next_level = get_next_level(points)

    # Progress to next level
    if next_level:
        points_needed = next_level['min_points'] - current_level['min_points']
        points_current = points - current_level['min_points']
        progress_pct = min(int((points_current / points_needed) * 10), 10)
        progress_bar = '█' * progress_pct + '░' * (10 - progress_pct)
        progress_text = f"\n📊 {progress_bar} {points_current}/{points_needed}"
        next_text = f"\n⬆️ Keyingi: {next_level['name'] if lang=='uz' else next_level['name_ru']}{progress_text}"
    else:
        next_text = "\n🌟 Maksimal darajaga yetdingiz!" if lang=='uz' else "\n🌟 Максимальный уровень достигнут!"

    # Streak display
    if streak == 0:
        streak_text = "0 kun (boshlang!)" if lang=='uz' else "0 дней (начните!)"
    elif streak >= 100:
        streak_text = f"🔥🔥🔥 {streak} kun — LEGEND!"
    elif streak >= 30:
        streak_text = f"🔥🔥 {streak} kun — Ustoz!"
    elif streak >= 7:
        streak_text = f"🔥 {streak} kun — Zo'r!"
    else:
        streak_text = f"⚡ {streak} kun"

    # Badges display (max 8 shown)
    if badges_list:
        badge_emojis = ' '.join([
            BADGES[b]['emoji']
            for b in badges_list[:8]
            if b in BADGES
        ])
        badges_text = f"\n🏅 Nishonlar: {badge_emojis}" if lang=='uz' else f"\n🏅 Значки: {badge_emojis}"
        if len(badges_list) > 8:
            badges_text += f" +{len(badges_list)-8}"
    else:
        badges_text = "\n🏅 Nishonlar: — (hali yo'q)" if lang=='uz' else "\n🏅 Значки: — (пока нет)"

    # Days since joined
    if isinstance(join_date, datetime):
        days_member = (datetime.utcnow() - join_date).days
        join_str = join_date.strftime('%d.%m.%Y')
    else:
        days_member = 0
        join_str = str(join_date)

    profile = f"""⭐ PROFIL MA'LUMOTLARI
━━━━━━━━━━━━━━━━━━━━━

🆔 ID: {user_id}
👤 Ism: {name}
📅 A'zo: {join_str} ({days_member} kun)

━━━━━━━━━━━━━━━━━━━━━
🏆 DARAJA VA BALL
━━━━━━━━━━━━━━━━━━━━━

{current_level['name'] if lang=='uz' else current_level['name_ru']}{next_text}
⭐ Jami ball: {points:,}

━━━━━━━━━━━━━━━━━━━━━
📊 FAOLIYAT
━━━━━━━━━━━━━━━━━━━━━

📥 Yuklanganlar: {downloads} ta
🎨 Creator: {creator_uses} marta
👥 Taklif: {referrals} kishi
{streak_text}
📈 Eng uzun streak: {longest_streak} kun
{badges_text}

━━━━━━━━━━━━━━━━━━━━━
💎 HISOB
━━━━━━━━━━━━━━━━━━━━━

⚡ Kredit: {credits} ta
💰 Donat qilish: /donate

━━━━━━━━━━━━━━━━━━━━━
✨ SpeedLoad — ijodingiz uchun eng yaxshi do'st!
Siz bilan ishlash — bizning sharafimiz! 🙏"""

    return profile

# === 6. NOTIFICATIONS ===

STREAK_MESSAGES = {
    'uz': {
        'streak_3':    "🔥 3 kunlik streak! Zo'r boshlanish, {name}! Davom eting!",
        'streak_7':    "⚡ 7 KUNLIK STREAK! {name}, bu jiddiy! +25 bonus ball oldingiz! 🎁",
        'streak_14':   "🌟 2 haftalik streak, {name}! Siz haqiqiy sodiq foydalanuvchisiz!",
        'streak_30':   "🏆 30 KUNLIK STREAK! {name}, bu AJOYIB! +100 bonus ball! 🎉\nBu statistikani do'stlaringizga ko'rsating!",
        'streak_100':  "👑 100 KUNLIK STREAK, {name}!!! LEGEND STATUS! +500 ball! 🌟\nSiz SpeedLoad tarixi! Rahmat!",
        'streak_broken': "💔 {name}, streak uzildi... {streak} kunlik streak ketdi.\nLekin xafa bo'lmang — bugundan yangi streak boshlang! 💪\n\n🎯 Har kuni foydalansangiz — streak davom etadi!",
        'new_streak':  "✨ {name}, streakingiz boshlandi! Har kuni foydalanib davom eting! 🔥",
    },
    'ru': {
        'streak_3':    "🔥 3-дневный стрик! Отличное начало, {name}!",
        'streak_7':    "⚡ 7-ДНЕВНЫЙ СТРИК! {name}, серьёзно! +25 бонусных баллов! 🎁",
        'streak_30':   "🏆 30-ДНЕВНЫЙ СТРИК! {name}, это НЕВЕРОЯТНО! +100 баллов! 🎉",
        'streak_broken': "💔 {name}, стрик прерван... {streak} дней ушло.\nНе расстраивайтесь — начните новый стрик сегодня! 💪",
    }
}

def get_level_up_msg(level: int, lang: str = 'uz') -> str:
    messages_uz = {
        2: "⚡ Endi siz faol foydalanuvchisiz! Zo'r start!",
        3: "🎯 Ijodkor bo'ldingiz! Creator vositalari sizni kutayapti!",
        4: "🔥 Pro darajasiga yetdingiz! Haqiqiy professional!",
        5: "💎 Creator darajasi! Siz haqiqiy ijodkorsiz!",
        6: "🏆 Expert! Bot ichida naq ustasiz!",
        7: "🌟 MASTER CREATOR! O'zbekistondagi eng yaxshi ijodkorlardan biri!",
        8: "👑 LEGEND STATUS! Siz tarixga kirdingiz! Hamma sizga qaraydi!",
    }
    messages_ru = {
        2: "⚡ Теперь вы активный пользователь! Отличный старт!",
        3: "🎯 Вы стали Творцом! Инструменты Creator ждут вас!",
        4: "🔥 Вы достигли уровня Pro! Настоящий профессионал!",
        5: "💎 Уровень Creator! Вы настоящий созидатель!",
        6: "🏆 Эксперт! Вы настоящий мастер в боте!",
        7: "🌟 МАСТЕР КРИЭЙТОР! Один из лучших в Узбекистане!",
        8: "👑 СТАТУС ЛЕГЕНДЫ! Вы вошли в историю! Все смотрят на вас!",
    }
    return messages_uz.get(level, "💪 Zo'r natija!") if lang == 'uz' else messages_ru.get(level, "💪 Отличный результат!")

# === 7. LEADERBOARD ===

def format_leaderboard(top_users: list, lang: str = 'uz') -> str:
    medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

    lines = []
    for i, user in enumerate(top_users):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        name = (user.first_name or "Foydalanuvchi")[:15]
        count = user.weekly_downloads or 0
        lines.append(f"{medal} {name} — {count} ta")

    board = '\n'.join(lines) if lines else ("Hali hech kim yo'q!" if lang=='uz' else "Пока никого нет!")

    header = {
        'uz': f"""🏆 HAFTALIK REYTING
━━━━━━━━━━━━━━━━━━
{board}
━━━━━━━━━━━━━━━━━━
📊 Eng ko'p yuklab olganlar!
🔄 Har dushanba yangilanadi""",

        'ru': f"""🏆 ЕЖЕНЕДЕЛЬНЫЙ РЕЙТИНГ
━━━━━━━━━━━━━━━━━━
{board}
━━━━━━━━━━━━━━━━━━
🔄 Обновляется каждый понедельник""",
    }

    return header.get(lang, header['uz'])
