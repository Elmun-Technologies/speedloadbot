import asyncio
import sys
import os
from sqlalchemy import text
from database.connection import engine

async def run_migration():
    print("🚀 Starting database migration for Trend Radar...")
    
    async with engine.begin() as conn:
        commands = [
            """
            CREATE TABLE IF NOT EXISTS trends (
                id SERIAL PRIMARY KEY,
                week_number VARCHAR(10),
                category VARCHAR(50),
                title VARCHAR(200),
                description TEXT,
                example_link VARCHAR(500),
                example_search VARCHAR(200),
                music_name VARCHAR(200),
                music_artist VARCHAR(200),
                growth_percent INTEGER DEFAULT 0,
                views_per_day VARCHAR(50),
                how_to_use TEXT,
                why_it_works TEXT,
                platforms TEXT DEFAULT '[]',
                lang VARCHAR(5) DEFAULT 'uz',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS trend_views (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                trend_id INTEGER REFERENCES trends(id),
                viewed_at TIMESTAMP DEFAULT NOW()
            );
            """
        ]
        
        for cmd in commands:
            try:
                print(f"Executing migration step...")
                await conn.execute(text(cmd))
            except Exception as e:
                print(f"⚠️ Error: {e}")

    print("✅ Trend Radar migration completed!")

if __name__ == "__main__":
    asyncio.run(run_migration())
