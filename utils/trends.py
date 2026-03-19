import random
import json
from datetime import datetime
import pytz
from config import OPENAI_API_KEY

# === AI TREND RESEARCH ===

async def research_weekly_trends(openai_client, week: str) -> list:
    """
    AI researches current trends and formats them for the bot.
    """
    prompt = f"""Bugun: {week}

Sen ijtimoiy tarmoqlar trend mutaxassisisan.
O'zbekiston va MDH bozori uchun hozir eng ko'p ishlatiladigan
Instagram Reels va TikTok trendlarini tahlil qil.

Quyidagi formatda 5 ta trend ber (JSON):

[
  {{
    "category": "music|format|challenge|effect",
    "title": "Trend nomi",
    "description": "Qisqacha tavsif (1 jumla, o'zbek tilida)",
    "music_name": "Musiqa nomi (agar music trend bo'lsa)",
    "music_artist": "Artist",
    "growth_percent": 250,
    "views_per_day": "1.5M",
    "how_to_use": "Bu trenddan qanday foydalanish bo'yicha ANIQ maslahat (o'zbek tilida, 2-3 jumla)",
    "example_search": "YouTube yoki Instagram da qidirish uchun kalit so'z",
    "platforms": ["instagram", "tiktok"],
    "why_it_works": "Psixologik sabab — nima uchun bu trend ishlayapti"
  }}
]

Faqat JSON qaytar, boshqa hech narsa yozma.
Trendlar HOZIR (2026 yil mart) dolzarb bo'lishi kerak.
O'zbek va MDH auditoriyasiga mos bo'lishi kerak."""

    response = await openai_client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'system', 'content': 'You are a trend research assistant.'},
                  {'role': 'user', 'content': prompt}],
        temperature=0.7,
        max_tokens=2000,
    )

    content = response.choices[0].message.content
    cleaned = content.replace('```json', '').replace('```', '').strip()
    return json.loads(cleaned)

# === TREND FORMATTING ===

def format_trend_card(trend: dict, index: int, total: int, lang: str = 'uz') -> str:
    category_icons = {
        'music':     '🎵',
        'format':    '📐',
        'challenge': '🏆',
        'effect':    '✨',
        'audio':     '🔊',
    }
    cat_icon = category_icons.get(trend.get('category', 'music'), '🔥')

    growth = trend.get('growth_percent', 0)
    views = trend.get('views_per_day', 'N/A')

    if growth >= 300:
        growth_badge = f"🚀 +{growth}% — VIRAL!"
    elif growth >= 200:
        growth_badge = f"🔥 +{growth}% — Juda tez o'smoqda"
    elif growth >= 100:
        growth_badge = f"📈 +{growth}% — O'sishda"
    else:
        growth_badge = f"📊 +{growth}%"

    platforms = trend.get('platforms', [])
    if isinstance(platforms, str):
        try: platforms = json.loads(platforms)
        except: platforms = []

    platform_icons = {
        'instagram': '📸',
        'tiktok': '🎵',
        'youtube': '▶️',
        'facebook': '📘',
    }
    platform_str = ' '.join([platform_icons.get(p, '📱') for p in platforms])

    example_link = trend.get('example_link', '')
    link_text = f"\n🔗 Namuna: {example_link}" if example_link else \
                f"\n🔍 Qidiring: \"{trend.get('example_search', trend.get('title'))}\""

    if lang == 'uz':
        return f"""{cat_icon} TREND #{index}/{total}
━━━━━━━━━━━━━━━━━━

🎯 {trend['title']}
{platform_str}

📊 {growth_badge}
👁 Kunlik ko'rishlar: {views}

📝 {trend.get('description', '')}

💡 Qanday ishlating:
{trend.get('how_to_use', '')}

🧠 Nima uchun ishlaydi:
{trend.get('why_it_works', '')}
{link_text}

━━━━━━━━━━━━━━━━━━
⏰ Trenddan foydalaning — vaqt cheklangan!"""
    else:
        return f"""{cat_icon} ТРЕНД #{index}/{total}
━━━━━━━━━━━━━━━━━━

🎯 {trend['title']}
{platform_str}

📊 {growth_badge}
👁 Просмотров в день: {views}

📝 {trend.get('description', '')}

💡 Как использовать:
{trend.get('how_to_use', '')}
{link_text}

━━━━━━━━━━━━━━━━━━
⏰ Используй тренд — пока не поздно!"""

def format_trend_radar_intro(week_label: str, lang: str = 'uz') -> str:
    if lang == 'uz':
        return f"""🔥 TREND RADAR — {week_label}
━━━━━━━━━━━━━━━━━━━━━

Salom! Bu hafta Instagram Reels va TikTok da
eng ko'p viral bo'layotgan trendlar — HAQIQIY raqamlar bilan!

✅ Faqat ishlayotgan trendlar
✅ O'zbek va MDH auditoriyasiga mos
✅ Qanday ishlatish bo'yicha aniq maslahat
✅ Real havolalar bilan

👇 Boshlaylik..."""
    else:
        return f"""🔥 TREND RADAR — {week_label}
━━━━━━━━━━━━━━━━━━━━━

Привет! Это самые вирусные тренды недели
для Instagram Reels и TikTok — с реальными цифрами!

✅ Только работающие тренды
✅ Подходят для СНГ аудитории
✅ Конкретные советы по использованию

👇 Начнём..."""

def format_trend_radar_outro(total: int, lang: str = 'uz') -> str:
    if lang == 'uz':
        return f"""✅ HAFTALIK {total} TA TREND KO'RILDI!

💡 ESLATMA:
- Trenddan foydalanish uchun TEZLIK muhim
- Trend paydo bo'lganining 1-2 haftasi eng samarali
- Sifatli kontent + trend = viral imkoniyati

📢 Har DUSHANBA yangi trendlar!
🔔 Bildirishnoma olish uchun botda qoling!

🚀 Omad! Sizning videongiz viral bo'lishini kutamiz!"""
    else:
        return f"""✅ {total} ТРЕНДОВ ПРОСМОТРЕНО!

💡 ВАЖНО:
- Скорость использования тренда критична
- Первые 1-2 недели после появления — самые эффективные
- Качественный контент + тренд = шанс на вирусность

📢 Каждый ПОНЕДЕЛЬНИК новые тренды!
🚀 Удачи! Ждём ваш вирусный ролик!"""

def get_week_label(lang: str = 'uz') -> str:
    tashkent = pytz.timezone('Asia/Tashkent')
    now = datetime.now(tashkent)
    week_num = now.strftime('%W')
    month_names_uz = ['', 'Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun', 'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr']
    month_names_ru = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    month = now.month
    year = now.year
    if lang == 'uz':
        return f"{month_names_uz[month]} {year} — {week_num}-hafta"
    return f"{month_names_ru[month]} {year} — {week_num} неделя"
