import os
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update, and_
from typing import List, Optional
from pydantic import BaseModel

from database.connection import AsyncSessionLocal
from database.models import User, Download, Ticket, TicketReply, Trend, Payment, TicketStatus
from config import JWT_SECRET

app = FastAPI(title="SpeedLoad Admin API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Middleware
def verify_admin_token(req: Request):
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

# DB Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --- ADMIN ENDPOINTS ---

@app.get("/admin/stats", dependencies=[Depends(verify_admin_token)])
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_users = await db.scalar(select(func.count(User.id)))
    total_downloads = await db.scalar(select(func.count(Download.id)))
    open_tickets = await db.scalar(select(func.count(Ticket.id)).where(Ticket.status != TicketStatus.closed))
    
    # Active today (last 24h)
    today_threshold = datetime.utcnow() - timedelta(days=1)
    active_today = await db.scalar(select(func.count(User.id)).where(User.last_active >= today_threshold))
    
    # Downloads today
    downloads_today = await db.scalar(select(func.count(Download.id)).where(Download.created_at >= today_threshold))
    
    # New users today
    new_users_today = await db.scalar(select(func.count(User.id)).where(User.created_at >= today_threshold))
    
    # Revenue (dummy for now as payments might not be real yet)
    revenue_today = await db.scalar(select(func.sum(Payment.amount)).where(Payment.created_at >= today_threshold)) or 0
    total_revenue = await db.scalar(select(func.sum(Payment.amount))) or 0

    return {
        "totalUsers": total_users,
        "activeToday": active_today,
        "activeWeek": active_today * 3, # Mock for now
        "totalDownloads": total_downloads,
        "downloadsToday": downloads_today,
        "creatorUsesToday": 15, # Mock
        "totalRevenue": float(total_revenue),
        "revenueToday": float(revenue_today),
        "openTickets": open_tickets,
        "newUsersToday": new_users_today,
        "newUsersWeek": new_users_today * 5, # Mock
        "topPlatform": "Instagram",
        "avgSessionMin": 4.5
    }

@app.get("/admin/stats/daily", dependencies=[Depends(verify_admin_token)])
async def get_daily_stats(days: int = 14, db: AsyncSession = Depends(get_db)):
    # Mock daily data for charts
    chart_data = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%m-%d")
        chart_data.append({
            "date": date,
            "active_users": 100 + (i * 5),
            "new_users": 10 + i,
            "downloads": 50 + (i * 10),
            "creator_uses": 5 + i
        })
    return list(reversed(chart_data))

@app.get("/admin/users", dependencies=[Depends(verify_admin_token)])
async def get_users(page: int = 1, search: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    limit = 20
    offset = (page - 1) * limit
    
    query = select(User).order_by(desc(User.created_at))
    if search:
        query = query.where(User.first_name.ilike(f"%{search}%"))
        
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
    ticket.status = "in_progress"
    await db.commit()
    
    # Here we would normally trigger a notification to the user via the bot
    # bot.send_message(ticket.user_id, f"Admin reply: {data.message}")
    
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
