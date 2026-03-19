import asyncio
import random
from datetime import datetime
import pytz
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

# === CONSTANTS ===
REDIRECT_VIDEO = "https://www.youtube.com/watch?v=DyunCIco-4Y"

HARMFUL_KEYWORDS = [
    # Adult content indicators
    'porn', 'xxx', 'onlyfans', 'adult', '18+site',
    'sex.', 'nude', 'naked',
    # Gambling
    'casino', 'bet365', 'mostbet', 'melbet', '1xbet',
    'stavka', 'ставка', 'казино',
    # Harmful
    'darkweb', 'dark web', 'tor browser',
]

QUOTES_UZ = [
    "💡 \"Har bir ekspert bir paytlar yangi boshlagan.\" — Helen Hayes",
    "🚀 \"Imkonsiz degan so'z faqat kichik odamlar lug'atida bor.\" — Napoleon",
    "🎯 \"Muvaffaqiyat — bu tasodif emas, bu to'g'ri qarorlar natijasidir.\"",
    "⚡ \"Bugun qilib bo'lmaydi deb o'ylagan narsangizni ertaga qilasiz.\" — Henry Ford",
    "💪 \"Qiyinchilik — bu imkoniyatning boshqa nomi.\" — Einstein",
    "🌟 \"Eng uzoq sayohat ham bitta qadamdan boshlanadi.\" — Lao Tzu",
    "🔥 \"Katta orzular ko'rmang — ULKAN orzular ko'ring!\"",
    "🎨 \"Ijod — bu aqlning o'yini, ruhning quvonchi.\"",
    "✨ \"Har kuni ozgina yaxshi ish qiling — hayot o'zgaradi.\"",
    "🏆 \"G'olib bo'lish uchun avval g'olib kabi o'ylash kerak.\"",
    "💎 \"Olmoslar ham bosim ostida hosil bo'ladi.\"",
    "🌱 \"Bugun ekkaning mevasi ertaga pishadi — sabr qiling.\"",
    "🦁 \"Qo'rqmaslik jasorat emas — qo'rqib ham harakat qilish jasorat!\"",
    "🎵 \"Hayot — bu improvizatsiya, nota emas.\"",
    "🌊 \"To'lqin kabi qattiq ur, suv kabi yumshoq bo'l.\" — O'zbek naql",
]

QUOTES_RU = [
    "💡 \"Каждый эксперт когда-то был новичком.\"",
    "🚀 \"Невозможное — это просто то, что ещё не сделано.\"",
    "🎯 \"Успех — это не случайность, это правильные решения каждый день.\"",
    "⚡ \"Действуй сейчас. Условия никогда не будут идеальными.\"",
    "💪 \"Трудности — это возможности в маскировке.\"",
    "🌟 \"Великий путь начинается с маленького шага.\"",
    "🔥 \"Мечтай смело — реализуй ещё смелее!\"",
    "✨ \"Каждый день — это новый шанс стать лучше.\"",
]

QUOTES_EN = [
    "💡 \"Every expert was once a beginner.\"",
    "🚀 \"The impossible is just the untried.\"",
    "🎯 \"Success is not an accident — it's a daily choice.\"",
    "⚡ \"Act now. Conditions will never be perfect.\"",
    "💪 \"Difficulties are opportunities in disguise.\"",
    "🌟 \"A great journey begins with a single step.\"",
    "🔥 \"Dream big — execute even bigger!\"",
]

# === CORE FUNCTIONS ===

async def send_typing(context: ContextTypes.DEFAULT_TYPE, chat_id: int, duration: float = None):
    if duration is None:
        duration = random.uniform(0.3, 0.6)
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(duration)

def get_smart_greeting(user_first_name: str, user_id: int) -> str:
    tashkent = pytz.timezone('Asia/Tashkent')
    now = datetime.now(tashkent)
    hour = now.hour
    weekday = now.weekday()  # 0=Monday, 4=Friday
    month = now.month
    day = now.day

    name = user_first_name or "Do'stim"

    # === HOLIDAYS (check first — highest priority) ===
    holidays = {
        (1, 1):  [
            f"🎊 Yangi yil muborak, {name}! Bu yil yangi rekordlar o'rnatamiz! Mening bilan bo'lganingiz uchun rahmat 🥂",
            f"🎉 {name}, Yangi yil bilan! Yaqinlaringiz bilan baxtli bo'ling! ✨"
        ],
        (3, 8):  [
            f"🌸 {name}, 8-mart muborak! Dunyo siz kabi ajoyib insonlardan go'zal! 🌹",
            f"💐 Bahor kabi nafis, nur kabi yorqin! 8-mart muborak, {name}! 🌺"
        ],
        (3, 21): [
            f"🌺 Navro'z muborak, {name}! Yangilanish fasli keldi — yangi g'oyalar vaqti! 🌿",
            f"☀️ Navro'z bayrami qutlug' bo'lsin! Bahor kabi yangilanaylik, {name}! 🌸"
        ],
        (5, 9):  [
            f"🎖️ Xotira va qadrlash kuni... Unutmaylik, {name}. Tinchlik — eng katta boylik 🕊️"
        ],
        (6, 1):  [
            f"👶 Bolalar himoyasi kuni muborak! Dunyo bolalar kulgi bilan to'lsin! 🌈"
        ],
        (9, 1):  [
            f"🇺🇿 Mustaqillik kuni muborak, {name}! Buyuk kelajak quraylik! 🌟",
            f"🎆 Mustaqillik — eng qimmatli boyligimiz! Muborak bo'lsin, {name}! 🇺🇿"
        ],
        (10, 1): [
            f"👩🏫 O'qituvchilar kuni muborak! Barcha ustozlarga hurmat! 📚"
        ],
        (12, 1): [
            f"🇺🇿 Konstitutsiya kuni muborak, {name}! Huquq va erkinlik — asosimiz! ⚖️"
        ],
        (12, 31): [
            f"🥂 {name}, yil oxirida ham mening bilan ekansiz! Rahmat! Yangi yil mubarak bo'lsin! 🎊",
            f"⏰ {name}, yil tugamoqda... Bugun qanday kunlar o'tdiki! Yangi yil bilan! 🎇"
        ],
    }

    # Check Ramazon (approximate dates, update yearly)
    ramazon_dates = [
        # 2025 Ramazon: March 1 - March 30
        (month == 3 and 1 <= day <= 30),
    ]
    if any(ramazon_dates):
        return random.choice([
            f"🌙 Ramazon muborak, {name}! Ro'za tutayotganlar uchun kuch va sabr tilaymiz! 🤲",
            f"✨ Muborak Ramazon oyi, {name}! Duolaringiz qabul bo'lsin! 🌙"
        ])

    if (month, day) in holidays:
        return random.choice(holidays[(month, day)])

    # === JUMA (Friday — special) ===
    if weekday == 4:  # Friday
        return random.choice([
            f"🤲 Juma muborak, {name}! Bugun eng muborak kun — yaxshi niyat bilan boshlang! 🌟",
            f"☪️ Juma muborak! {name}, bugun duo qilishni unutmang! Baraka topsin! 🤲",
            f"🌟 Juma keldi, {name}! Eng muborak kun — sahovat va shukr kuni! ✨",
            f"🤲 Juma muborak, {name}! Bugun kichik bir yaxshilik qiling — katta savob! 🌸"
        ])

    # === TIME-BASED GREETINGS ===
    if 5 <= hour < 9:
        messages = [
            f"🌅 Xayrli tong, {name}! Erta turganning yuzi yorug' — bugun zo'r kun bo'ladi! ☀️",
            f"🌄 Assalomu alaykum, {name}! Erta turgan qush ko'm-ko'k dalani ko'radi 🐦",
            f"☀️ Tong muborak, {name}! Yangi kun — yangi imkoniyatlar! Nima yaratamiz bugun? 🚀",
            f"🌞 Xayrli tong, {name}! Choy ichdingizmi? Ish boshlaylik! ☕",
        ]
    elif 9 <= hour < 12:
        messages = [
            f"💪 Xayrli kun, {name}! Ish qizib ketayapti, a? Zo'r ketayapsiz! 🔥",
            f"🌞 Salom, {name}! Bugun juda samarali kun bo'layapti! Davom eting! ✨",
            f"⚡ Hey {name}! Energiya to'la, g'oya to'la — bugun nima qilamiz? 🎯",
            f"🎯 {name}, xayrli kun! Maqsadga qarab — oldinga! 🚀",
        ]
    elif 12 <= hour < 14:
        messages = [
            f"🍽️ Peshin bo'ldi, {name}! Ovqatlandingizmi? Ovqatlanib oling, keyin davom etamiz 😄",
            f"☀️ Peshin muborak, {name}! Kichik dam olib yana davom eting! 💪",
            f"🌞 {name}, peshin keldi! Bugungi yarim yo'l bosib o'tildi — zo'r! 🎉",
        ]
    elif 14 <= hour < 17:
        messages = [
            f"☕ {name}, tushdan keyin sekinlashdingizmi? Bu normal! Kichik qahva ichib davom eting ☕",
            f"💡 Salom, {name}! Eng yaxshi g'oyalar tushdan keyin tug'iladi — shay bo'ling! 🌟",
            f"🎵 {name}, xayrli kun! Musiqa qo'yib ishlash samarani 2x oshiradi 😉",
        ]
    elif 17 <= hour < 20:
        messages = [
            f"🌆 Xayrli kech, {name}! Ish kuni yakunlanyapti — bugun nimalarga erishdingiz? 🎯",
            f"🌇 Oqshom muborak, {name}! Kechki ijod eng yaxshisi — ilhom kuchli bo'ladi! ✨",
            f"🌅 {name}, kun yakunlanyapti! Bugungi mehnat ertangi muvaffaqiyat! 💪",
        ]
    elif 20 <= hour < 23:
        messages = [
            f"🌙 Xayrli kech, {name}! Kechasi ham ijod qilayapsizmi? Zo'r dedektiv! 🔍",
            f"⭐ Salom, {name}! Tungi soatlar — eng tinch va ijodiy vaqt! 🌙",
            f"🌟 {name}, kech bo'ldi! Lekin eng yaxshi g'oyalar tunda tug'iladi! ✨",
            f"🎭 Tungi ijodkor, {name}! Dunyo uxlayapti, siz yaratyapsiz — bu juda kuchli! 💫",
        ]
    else:  # 23-5
        messages = [
            f"🌙 {name}, bu vaqtda ham ekansiz? Kech yotish sog'liqqa yomon, lekin ishtiyoq zo'r! 😄",
            f"⭐ Tungi serdor, {name}! Uxlab olganingiz yaxshi bo'lurdi, lekin... qanday bo'ldi? 😄",
            f"🌌 {name}, kechasi ham ishlamoqdami? Kuchli odam! Lekin dam olish ham muhim 💤",
        ]

    return random.choice(messages)

def get_quote(lang: str = 'uz') -> str:
    quotes = {
        'uz': QUOTES_UZ,
        'ru': QUOTES_RU,
        'en': QUOTES_EN,
    }
    return random.choice(quotes.get(lang, QUOTES_UZ))

def check_content_filter(text: str, user_lang: str = 'uz') -> dict:
    text_lower = text.lower()
    triggered = any(kw in text_lower for kw in HARMFUL_KEYWORDS)

    if not triggered:
        return {'triggered': False, 'message': ''}

    # Gentle, kind warning — NOT harsh
    messages = {
        'uz': f"""🌟 Do'stim, bu yerda sizga yordam bera olmayman.

Lekin sizga muhim bir narsa ko'rsatmoqchiman — bu sizning hayotingizni o'zgartirishi mumkin:

👇 {REDIRECT_VIDEO}

Vaqtingizni qimmatli narsalarga sarflang. Siz bunga loyiqsiz! 🤍""",

        'ru': f"""🌟 Друг, здесь я не могу помочь с этим.

Но хочу показать тебе кое-что важное — это может изменить твою жизнь:

👇 {REDIRECT_VIDEO}

Трать время на ценное. Ты этого достоин! 🤍""",

        'en': f"""🌟 Friend, I can't help with this here.

But I want to show you something important — it might change your life:

👇 {REDIRECT_VIDEO}

Spend your time on what truly matters. You deserve better! 🤍""",
    }

    return {
        'triggered': True,
        'message': messages.get(user_lang, messages['uz'])
    }

def get_nudge_message(feature: str, user_name: str, lang: str = 'uz'):
    # Only trigger 30% of the time
    if random.random() > 0.3:
        return None

    name = user_name or "Do'stim"

    nudges_uz = {
        'download': [
            f"✅ Mana! {name}, bu video sizga foydali bo'lishini umid qilaman 🎬\n\n💡 Aytgancha, Creator bo'limida videoni skriptga ham aylantira olasiz!",
            f"🎉 Tayyor, {name}! Endi bu videoni xohlaganingizcha ishlating!\n\n🔥 Trend Radar orqali hozir nima trend ekanini ham bilishingiz mumkin 👀",
            f"⚡ {name}, yuklab olindi! Sifat yaxshimi?\n\nAgar video hajmi katta bo'lsa — Video siqish funksiyamiz bor 📦",
        ],
        'creator': [
            f"🎨 {name}, zo'r! Creator vositalaridan foydalanayapsiz!\n\n💎 Do'stlaringizni taklif qiling — har biri uchun +3 kredit olasiz! 🎁",
            f"✨ Ajoyib, {name}! Ijodkorlik yo'lida oldinga! 🚀\n\nBugungi trendlarni ko'rdingizmi? Trend Radar sizni kutayapti 🔥",
        ],
        'general': [
            f"💡 {name}, bir savol: bugun nima yaratmoqchisiz? Yordam bera olishim mumkin! 😊",
            f"🌟 {name}, bilasizmi — do'stlaringizga ulashsangiz, ular ham foydalanadi VA siz kredit olasiz! Win-win 🎁",
            f"☕ {name}, choy ichib o'tiribsizmi? Bu orada yangi funksiyalarimiz bor — ko'ring! 👀",
        ]
    }

    nudges_ru = {
        'download': [
            f"✅ Готово! {name}, надеюсь видео пригодится! 🎬\n\n💡 Кстати, в разделе Creator можно превратить видео в скрипт!",
            f"🎉 {name}, загружено! Используй как хочешь!\n\n🔥 Хочешь знать что сейчас в тренде? Заходи в Trend Radar 👀",
        ],
        'general': [
            f"💡 {name}, один вопрос: что создаёшь сегодня? Могу помочь! 😊",
            f"🌟 {name}, знаешь что? Пригласи друзей — получишь кредиты! Win-win 🎁",
        ]
    }

    feature_nudges = {
        'uz': nudges_uz,
        'ru': nudges_ru,
    }.get(lang, nudges_uz)

    msgs = feature_nudges.get(feature, feature_nudges['general'])
    return random.choice(msgs)

def get_morning_message(lang: str = 'uz') -> str:
    tashkent = pytz.timezone('Asia/Tashkent')
    now = datetime.now(tashkent)
    weekday = now.weekday()
    day_names_uz = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
    day_name = day_names_uz[weekday]

    morning_uz = [
        f"🌅 Xayrli tong!\n\n📅 Bugun {day_name}\n\n{get_quote('uz')}\n\n💪 Bugun ham zo'r bo'ladi — ishonaman! Nima qilmoqchisiz?",
        f"☀️ Yangi kun, yangi imkoniyatlar!\n\n🎯 Bugun bitta maqsad qo'ying va bajaring!\n\n{get_quote('uz')}",
        f"🌄 Xayrli tong! {day_name} — yangi boshlanish!\n\n✨ {get_quote('uz')}\n\n🚀 Boshlaylik!",
    ]

    morning_ru = [
        f"🌅 Доброе утро!\n\n📅 Сегодня {day_name}\n\n{get_quote('ru')}\n\n💪 Сегодня будет отличный день!",
        f"☀️ Новый день — новые возможности!\n\n{get_quote('ru')}\n\n🚀 Поехали!",
    ]

    messages = {'uz': morning_uz, 'ru': morning_ru}
    return random.choice(messages.get(lang, morning_uz))

def get_weekly_challenge(lang: str = 'uz') -> str:
    challenges_uz = [
        "🏆 Haftalik vazifa!\n\n📌 Bu hafta 5 ta yangi video yuklab ko'ring!\nEng yaxshi ko'rganingizni @speedload_support ga yuboring — sovg'a bor! 🎁",
        "🔥 Haftalik challenge!\n\n📌 Creator vositalaridan 3 marta foydalaning!\nNatijangizni ulashing — kredit oling! ⚡",
        "🌟 Bu hafta maqsadingiz:\n\n📌 1 do'stingizga botni tavsiya qiling!\nUlar ro'yxatdan o'tsa — siz +3 kredit olasiz! 🎁",
    ]
    return random.choice(challenges_uz)

def format_profile(user_data: dict, lang: str = 'uz') -> str:
    name = user_data.get('name', 'Foydalanuvchi')
    user_id = user_data.get('id', '')
    join_date = user_data.get('join_date', datetime.now())
    downloads = user_data.get('downloads', 0)
    creator_uses = user_data.get('creator_uses', 0)
    referrals = user_data.get('referrals', 0)
    credits = user_data.get('credits', 0)
    streak = user_data.get('streak', 1)

    # Calculate days since joined
    days_ago = (datetime.now() - join_date).days
    if days_ago == 0:
        joined_text = "Bugun qo'shildi! 🎉"
    elif days_ago == 1:
        joined_text = "Kecha qo'shildi"
    else:
        joined_text = f"{days_ago} kun oldin"

    # Status based on activity
    if downloads >= 500 or creator_uses >= 100:
        status = "👑 VIP Ijodkor"
        next_level = ""
    elif downloads >= 100 or creator_uses >= 20:
        status = "🥇 Gold Ijodkor"
        next_level = f"⬆️ VIP uchun: {500 - downloads} ta yuklab olish"
    elif downloads >= 50 or creator_uses >= 10:
        status = "🥈 Silver Foydalanuvchi"
        next_level = f"⬆️ Gold uchun: {100 - downloads} ta yuklab olish"
    else:
        status = "🌱 Yangi Foydalanuvchi"
        next_level = f"⬆️ Silver uchun: {50 - downloads} ta yuklab olish"

    # Streak emoji
    streak_emoji = "🔥" if streak >= 7 else "⚡" if streak >= 3 else "✨"

    profile_uz = f"""⭐ PROFIL MA'LUMOTLARI
━━━━━━━━━━━━━━━━━━━━━

🆔 ID: {user_id}
👤 Ism: {name}
📅 A'zo bo'lgan: {join_date.strftime('%d.%m.%Y')} ({joined_text})
🌍 Til: O'zbekcha

━━━━━━━━━━━━━━━━━━━━━
📊 FAOLIYAT STATISTIKASI
━━━━━━━━━━━━━━━━━━━━━

📥 Yuklangan: {downloads} ta video
🎨 Creator vositalari: {creator_uses} marta
👥 Taklif qilinganlar: {referrals} kishi
{streak_emoji} Streak: {streak} kun ketma-ket

━━━━━━━━━━━━━━━━━━━━━
💎 HISOB HOLATI
━━━━━━━━━━━━━━━━━━━━━

⚡ Kredit: {credits} ta
🏅 Status: {status}
{next_level}

━━━━━━━━━━━━━━━━━━━━━
✨ SpeedLoad — ijodingiz uchun eng yaxshi do'st!
Siz bilan ishlash — bizning sharafimiz! 🙏"""

    return profile_uz
