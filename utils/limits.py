from datetime import datetime, timedelta
from database.models import User

def evaluate_resets(user: User):
    now = datetime.utcnow()
    
    if now >= user.last_6h_reset + timedelta(hours=6):
        user.downloads_6h = 5
        user.last_6h_reset = now

    if now >= user.last_week_reset + timedelta(days=7):
        user.downloads_week = 0
        user.last_week_reset = now

def get_time_left(reset_time: datetime, duration: timedelta) -> str:
    now = datetime.utcnow()
    target = reset_time + duration
    if target <= now:
        return "0 daqiqa"
    
    diff = target - now
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours > 0:
        return f"{hours} soat {minutes} daqiqa"
    return f"{minutes} daqiqa"
