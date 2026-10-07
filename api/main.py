import hmac
import logging
from datetime import datetime, timedelta

import jwt
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from typing import Optional
from pydantic import BaseModel

from database.connection import AsyncSessionLocal
from database.models import User, Download, Ticket, TicketReply, Trend, Payment, TicketStatus
from config import JWT_SECRET, ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_CORS_ORIGINS

logger = logging.getLogger("speedload.api")

app = FastAPI(title="SpeedLoad Admin API")

if not JWT_SECRET:
    logger.warning(
        "JWT_SECRET is not set! Admin login will be disabled until it is configured. "
        "Set it in your .env file."
    )
elif len(JWT_SECRET) < 32:
    logger.warning(
        "JWT_SECRET is shorter than 32 characters — use a long random string "
        "(e.g. `python -c \"import secrets; print(secrets.token_hex(32))\"`)."
    )

# CORS — only the configured dashboard origins are allowed (never a wildcard
# together with credentials in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ADMIN_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- HEALTH CHECK ---

@app.get("/health")
async def health():
    return {"status": "ok"}


# --- ADMIN DASHBOARD (static, no build step) ---

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "dashboard"


@app.get("/")
async def dashboard_home():
    """Serve the built-in admin dashboard (dashboard/index.html)."""
    index = DASHBOARD_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(index)


@app.get("/dashboard")
async def dashboard_page():
    return await dashboard_home()


# --- AUTH ---

def verify_admin_token(req: Request):
    if not JWT_SECRET:
        raise HTTPException(status_code=500, detail="Server misconfigured: JWT_SECRET is not set")
    auth_header = req.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Forbidden")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/admin/login")
async def admin_login(data: LoginRequest):
    """Exchange admin credentials for a JWT (valid for 12 hours)."""
    if not JWT_SECRET:
        raise HTTPException(status_code=500, detail="Server misconfigured: JWT_SECRET is not set")
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=500, detail="Server misconfigured: ADMIN_PASSWORD is not set")

    username_ok = hmac.compare_digest(data.username, ADMIN_USERNAME)
    password_ok = hmac.compare_digest(data.password, ADMIN_PASSWORD)
    if not (username_ok and password_ok):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    now = datetime.utcnow()
    expires = now + timedelta(hours=12)
    token = jwt.encode(
        {"role": "admin", "sub": data.username, "iat": now, "exp": expires},
        JWT_SECRET,
        algorithm="HS256",
    )
    return {"token": token, "token_type": "bearer", "expires_in": 12 * 3600}


# DB Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# --- ADMIN ENDPOINTS ---

@app.get("/admin/stats", dependencies=[Depends(verify_admin_token)])
async def get_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    total_users = await db.scalar(select(func.count(User.id)))
    total_downloads = await db.scalar(select(func.count(Download.id)))
    open_tickets = await db.scalar(select(func.count(Ticket.id)).where(Ticket.status != TicketStatus.closed))

    active_today = await db.scalar(select(func.count(User.id)).where(User.last_active >= day_ago))
    active_week = await db.scalar(select(func.count(User.id)).where(User.last_active >= week_ago))

    downloads_today = await db.scalar(select(func.count(Download.id)).where(Download.created_at >= day_ago))
    new_users_today = await db.scalar(select(func.count(User.id)).where(User.created_at >= day_ago))
    new_users_week = await db.scalar(select(func.count(User.id)).where(User.created_at >= week_ago))

    revenue_today = await db.scalar(select(func.sum(Payment.amount)).where(Payment.created_at >= day_ago)) or 0
    total_revenue = await db.scalar(select(func.sum(Payment.amount))) or 0

    # Creator tool uses "today" — daily counters are reset by the streak logic each day
    creator_uses_today = await db.scalar(select(func.sum(User.daily_creator_uses))) or 0

    top_platform_row = (await db.execute(
        select(Download.platform, func.count(Download.id).label("cnt"))
        .group_by(Download.platform)
        .order_by(desc("cnt"))
        .limit(1)
    )).first()

    return {
        "totalUsers": total_users,
        "activeToday": active_today,
        "activeWeek": active_week,
        "totalDownloads": total_downloads,
        "downloadsToday": downloads_today,
        "creatorUsesToday": int(creator_uses_today or 0),
        "totalRevenue": float(total_revenue or 0),
        "revenueToday": float(revenue_today or 0),
        "openTickets": open_tickets,
        "newUsersToday": new_users_today,
        "newUsersWeek": new_users_week,
        "topPlatform": top_platform_row[0] if top_platform_row else None,
    }


@app.get("/admin/stats/daily", dependencies=[Depends(verify_admin_token)])
async def get_daily_stats(days: int = 14, db: AsyncSession = Depends(get_db)):
    """Real per-day aggregates (new users & downloads) for the last `days` days."""
    days = max(1, min(days, 90))
    chart_data = []
    for i in range(days):
        day = (datetime.utcnow() - timedelta(days=i)).date()
        next_day = day + timedelta(days=1)
        new_users = await db.scalar(
            select(func.count(User.id)).where(User.created_at >= day, User.created_at < next_day)
        )
        downloads = await db.scalar(
            select(func.count(Download.id)).where(Download.created_at >= day, Download.created_at < next_day)
        )
        chart_data.append({
            "date": day.strftime("%m-%d"),
            "new_users": new_users,
            "downloads": downloads,
        })
    return list(reversed(chart_data))


@app.get("/admin/users", dependencies=[Depends(verify_admin_token)])
async def get_users(page: int = 1, search: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    limit = 20
    offset = (page - 1) * limit

    query = select(User).order_by(desc(User.created_at))
    if search:
        query = query.where(or_(User.first_name.ilike(f"%{search}%"), User.username.ilike(f"%{search}%")))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.limit(limit).offset(offset))
    users = result.scalars().all()

    return {
        "users": [{
            "id": u.id,
            "telegram_id": u.telegram_id,
            "name": u.first_name,
            "username": u.username,
            "lang": u.language,
            "credits": u.credits,
            "streak_days": u.streak_days,
            "total_downloads": u.total_downloads,
            "created_at": u.created_at,
            "status": "blocked" if u.is_banned else "active"
        } for u in users],
        "total": total
    }


@app.post("/admin/users/{user_id}/block", dependencies=[Depends(verify_admin_token)])
async def block_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(status_code=404)
    user.is_banned = not user.is_banned
    await db.commit()
    return {"status": "success", "is_banned": user.is_banned}


class CreditUpdate(BaseModel):
    amount: int


@app.post("/admin/users/{user_id}/credits", dependencies=[Depends(verify_admin_token)])
async def add_credits(user_id: int, data: CreditUpdate, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(status_code=404)
    user.credits += data.amount
    await db.commit()
    return {"status": "success", "credits": user.credits}


@app.get("/admin/tickets", dependencies=[Depends(verify_admin_token)])
async def get_tickets(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Ticket).order_by(desc(Ticket.created_at))
    if status:
        query = query.where(Ticket.status == status)

    result = await db.execute(query)
    tickets = result.scalars().all()
    return {"tickets": tickets}


class ReplyData(BaseModel):
    message: str


@app.post("/admin/tickets/{ticket_id}/reply", dependencies=[Depends(verify_admin_token)])
async def reply_ticket(ticket_id: int, data: ReplyData, db: AsyncSession = Depends(get_db)):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket: raise HTTPException(status_code=404)

    reply = TicketReply(ticket_id=ticket_id, message=data.message)
    db.add(reply)
    ticket.status = TicketStatus.in_progress
    await db.commit()

    # NOTE: to notify the user via the bot, wire this to a shared task queue
    # or a bot webhook — left as a hook for a later phase.
    return {"status": "success"}


@app.get("/admin/trends", dependencies=[Depends(verify_admin_token)])
async def get_trends(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trend).where(Trend.is_active == True))
    return {"trends": result.scalars().all()}


@app.post("/admin/trends", dependencies=[Depends(verify_admin_token)])
async def add_trend_api(data: dict, db: AsyncSession = Depends(get_db)):
    trend = Trend(**data)
    db.add(trend)
    await db.commit()
    await db.refresh(trend)
    return {"status": "success", "trend": trend}


@app.delete("/admin/trends/{trend_id}", dependencies=[Depends(verify_admin_token)])
async def delete_trend(trend_id: int, db: AsyncSession = Depends(get_db)):
    trend = await db.get(Trend, trend_id)
    if trend:
        trend.is_active = False
        await db.commit()
    return {"status": "success"}


@app.get("/admin/payments", dependencies=[Depends(verify_admin_token)])
async def get_payments(page: int = 1, db: AsyncSession = Depends(get_db)):
    limit = 20
    offset = (page - 1) * limit
    result = await db.execute(select(Payment).order_by(desc(Payment.created_at)).limit(limit).offset(offset))
    return {"payments": result.scalars().all()}
