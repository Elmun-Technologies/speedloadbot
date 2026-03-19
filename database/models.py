from sqlalchemy import Column, BigInteger, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database.connection import Base

class DownloadStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    
    language = Column(String(2), default="uz")
    
    # Gamification & Streaks
    streak_days = Column(Integer, default=0)
    streak_last_date = Column(DateTime, nullable=True) # Using DateTime for consistency with existing codebase
    streak_longest = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    badges = Column(Text, default='[]') # JSON list
    
    # Activity Tracking (Daily/Weekly)
    daily_downloads = Column(Integer, default=0)
    daily_creator_uses = Column(Integer, default=0)
    daily_reset_date = Column(DateTime, nullable=True)
    weekly_downloads = Column(Integer, default=0)
    weekly_reset_date = Column(String, nullable=True) # Store as '2026-W12'
    
    # Lifetime Stats
    total_downloads = Column(Integer, default=0)
    total_creator_uses = Column(Integer, default=0)
    total_referrals = Column(Integer, default=0)
    
    # Economy
    credits = Column(Integer, default=5)
    referral_code = Column(String, unique=True, index=True)
    referred_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    
    # Legacy/Old fields (kept for compatibility or internal state)
    downloads_6h = Column(Integer, default=5)
    downloads_week = Column(Integer, default=0)
    last_6h_reset = Column(DateTime, default=datetime.utcnow)
    last_week_reset = Column(DateTime, default=datetime.utcnow)
    referral_bonus = Column(Integer, default=0) # Kept as legacy or separate bonus
    
    # Onboarding & Data Collection
    interests = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    onboarding_completed = Column(Boolean, default=False)

    # Creator Tools & Monetization
    creator_credits = Column(Integer, default=3) # PTB uses this, I'll keep it or sync it with 'credits'
    is_premium = Column(Boolean, default=False)
    
    # Engagement Tracking
    action_count = Column(Integer, default=0)
    
    is_banned = Column(Boolean, default=False)
    last_active = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    downloads = relationship("Download", back_populates="user")
    referrals_made = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    referrals_received = relationship("Referral", foreign_keys="Referral.referred_id", back_populates="referred")

class Download(Base):
    __tablename__ = "downloads"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    url = Column(Text, nullable=False)
    platform = Column(String) 
    title = Column(String, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    quality = Column(String) 
    duration = Column(Integer, nullable=True)
    status = Column(Enum(DownloadStatus, name="downloadstatus", native_enum=False), default=DownloadStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="downloads")

class Referral(Base):
    __tablename__ = "referrals"

    id = Column(BigInteger, primary_key=True, index=True)
    referrer_id = Column(BigInteger, ForeignKey("users.id"))
    referred_id = Column(BigInteger, ForeignKey("users.id"))
    coins_earned = Column(Integer, default=2) 
    created_at = Column(DateTime, default=datetime.utcnow)

    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referrals_received")

class Trend(Base):
    __tablename__ = "trends"
    
    id = Column(Integer, primary_key=True)
    week_number = Column(String(10)) # e.g. "2026-W12"
    category = Column(String(50)) # 'music', 'format', 'challenge', 'effect'
    title = Column(String(200))
    description = Column(Text)
    example_link = Column(String(500), nullable=True)
    example_search = Column(String(200), nullable=True)
    music_name = Column(String(200), nullable=True)
    music_artist = Column(String(200), nullable=True)
    growth_percent = Column(Integer, default=0)
    views_per_day = Column(String(50), nullable=True)
    how_to_use = Column(Text)
    why_it_works = Column(Text, nullable=True)
    platforms = Column(Text, default='[]') # JSON list
    lang = Column(String(5), default='uz')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TrendView(Base):
    __tablename__ = "trend_views"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    trend_id = Column(Integer, ForeignKey("trends.id"), nullable=True)
    viewed_at = Column(DateTime, default=datetime.utcnow)

class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"

class TicketType(str, enum.Enum):
    complaint = "complaint"
    request = "request"
    partner = "partner"
    other = "other"

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    user_name = Column(String)
    type = Column(Enum(TicketType, name="tickettype", native_enum=False), default=TicketType.other)
    message = Column(Text, nullable=False)
    screenshot_url = Column(String, nullable=True)
    status = Column(Enum(TicketStatus, name="ticketstatus", native_enum=False), default=TicketStatus.open)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    replies = relationship("TicketReply", back_populates="ticket")

class TicketReply(Base):
    __tablename__ = "ticket_replies"
    
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    ticket = relationship("Ticket", back_populates="replies")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    amount = Column(Integer) # in points/credits or cents? Assuming credits based on context
    currency = Column(String(10), default="USD")
    status = Column(String(20), default="completed") # completed, pending, failed
    provider = Column(String(50), nullable=True) # click, payme, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
