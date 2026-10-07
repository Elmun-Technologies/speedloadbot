"""Integration tests for the admin API against a real (SQLite) database.

Uses FastAPI's TestClient with the DB dependency overridden to a test
database, and seeds real rows through the actual CRUD layer.
"""
import asyncio

import pytest

pytest.importorskip("aiosqlite")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import api.main as api_main
from database import crud
from database.connection import Base
from database.models import Payment, Ticket, TicketType

TEST_JWT_SECRET = "test-secret-key-for-integration-tests-0123456789abcdef"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/api_test.db")

    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with SessionLocal() as s:
            u1 = await crud.create_user(s, 1001, "ali", "Ali", "uz")
            u2 = await crud.create_user(s, 1002, "vali", "Vali", "ru")
            await crud.create_download(s, u1.id, "https://youtu.be/abc", "youtube", "720p", "Video A", 60)
            await crud.create_download(s, u1.id, "https://youtu.be/def", "youtube", "360p", "Video B", 30)
            await crud.create_download(s, u2.id, "https://instagram.com/reel/x", "instagram", "best", "Reel C", 15)
            s.add(Ticket(user_id=u1.id, user_name="Ali", type=TicketType.complaint, message="Salom"))
            s.add(Payment(user_id=u1.id, amount=100, currency="USD", status="completed"))
            await crud.add_trend(s, {
                "week_number": "2026-W15", "category": "music", "title": "T1",
                "description": "d", "growth_percent": 10, "how_to_use": "x", "lang": "uz",
            })
            await s.commit()

    asyncio.run(setup())

    monkeypatch.setattr(api_main, "JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr(api_main, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(api_main, "ADMIN_PASSWORD", "s3cret")

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with SessionLocal() as session:
            yield session

    api_main.app.dependency_overrides[api_main.get_db] = override_get_db
    yield TestClient(api_main.app)
    api_main.app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def login(client, password="s3cret"):
    r = client.post("/admin/login", json={"username": "admin", "password": password})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_login_rejects_wrong_password(client):
    r = client.post("/admin/login", json={"username": "admin", "password": "nope"})
    assert r.status_code == 401


def test_login_success_returns_bearer_token(client):
    r = client.post("/admin/login", json={"username": "admin", "password": "s3cret"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 43200
    assert body["token"]


def test_admin_endpoints_require_token(client):
    assert client.get("/admin/stats").status_code == 401
    assert client.get("/admin/stats", headers=auth("garbage")).status_code == 401
    assert client.get("/admin/users").status_code == 401
    assert client.get("/admin/tickets").status_code == 401


def test_stats_returns_real_data(client):
    r = client.get("/admin/stats", headers=auth(login(client)))
    assert r.status_code == 200
    d = r.json()
    assert d["totalUsers"] == 2
    assert d["activeToday"] == 2
    assert d["totalDownloads"] == 3
    assert d["downloadsToday"] == 3
    assert d["newUsersToday"] == 2
    assert d["openTickets"] == 1
    assert d["topPlatform"] == "youtube"
    assert d["totalRevenue"] == 100.0
    assert d["creatorUsesToday"] == 0


def test_users_list_and_search(client):
    token = login(client)
    r = client.get("/admin/users", headers=auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert {u["name"] for u in body["users"]} == {"Ali", "Vali"}

    r = client.get("/admin/users", params={"search": "ali"}, headers=auth(token))
    assert r.json()["total"] == 2  # "Ali" exactly; "Vali" contains "ali"
    # username search works too
    r = client.get("/admin/users", params={"search": "val"}, headers=auth(token))
    assert r.json()["total"] == 1


def test_block_and_credits(client):
    token = login(client)
    r = client.get("/admin/users", headers=auth(token))
    uid = r.json()["users"][0]["id"]

    r = client.post(f"/admin/users/{uid}/block", headers=auth(token))
    assert r.status_code == 200 and r.json()["is_banned"] is True

    r = client.post(f"/admin/users/{uid}/credits", json={"amount": 7}, headers=auth(token))
    assert r.json()["credits"] == 12  # 5 default + 7

    assert client.post("/admin/users/999999/block", headers=auth(token)).status_code == 404
    assert client.post("/admin/users/999999/credits", json={"amount": 1}, headers=auth(token)).status_code == 404


def test_tickets_list_and_reply(client):
    token = login(client)
    r = client.get("/admin/tickets", headers=auth(token))
    tickets = r.json()["tickets"]
    assert len(tickets) == 1 and tickets[0]["message"] == "Salom"

    tid = tickets[0]["id"]
    r = client.post(f"/admin/tickets/{tid}/reply", json={"message": "Javob"}, headers=auth(token))
    assert r.status_code == 200

    r = client.get("/admin/tickets", params={"status": "in_progress"}, headers=auth(token))
    assert len(r.json()["tickets"]) == 1
    r = client.get("/admin/tickets", params={"status": "open"}, headers=auth(token))
    assert len(r.json()["tickets"]) == 0


def test_trends_create_and_delete_via_api(client):
    token = login(client)
    r = client.get("/admin/trends", headers=auth(token))
    assert len(r.json()["trends"]) == 1

    r = client.post("/admin/trends", json={
        "week_number": "2026-W16", "category": "effect", "title": "New",
        "description": "d", "growth_percent": 5, "how_to_use": "x", "lang": "uz",
    }, headers=auth(token))
    assert r.status_code == 200
    tid = r.json()["trend"]["id"]

    r = client.delete(f"/admin/trends/{tid}", headers=auth(token))
    assert r.status_code == 200

    r = client.get("/admin/trends", headers=auth(token))
    # the new trend is deactivated; only the seeded active one remains
    assert len(r.json()["trends"]) == 1


def test_daily_stats_shape(client):
    token = login(client)
    r = client.get("/admin/stats/daily", params={"days": 7}, headers=auth(token))
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 7
    today = data[-1]
    assert today["new_users"] == 2
    assert today["downloads"] == 3


def test_payments_list(client):
    token = login(client)
    r = client.get("/admin/payments", headers=auth(token))
    payments = r.json()["payments"]
    assert len(payments) == 1
    assert payments[0]["amount"] == 100
