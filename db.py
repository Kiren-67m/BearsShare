"""
db.py – Database layer for Bears Share.

Uses SQLAlchemy so the same code runs on:
  - SQLite locally (default, zero setup — creates bears_share.db)
  - PostgreSQL in production (set DATABASE_URL on Render)

Tables:
  subscribers  – the opt-in mailing list (imported from PantrySoft CSV export)
  suppression  – emails that clicked unsubscribe; filtered out of every send,
                 permanently, even if the subscriber list is re-imported
  send_log     – one row per broadcast, for the /history page
"""

from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Integer, String, Text, create_engine, select,
)
from sqlalchemy.orm import Session, declarative_base

import config


def _normalize_url(url: str) -> str:
    # Render's Postgres gives postgres:// URLs; SQLAlchemy needs postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


engine = create_engine(_normalize_url(config.DATABASE_URL), future=True)
Base = declarative_base()


class Subscriber(Base):
    __tablename__ = "subscribers"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), default="")
    email = Column(String(320), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Suppression(Base):
    __tablename__ = "suppression"
    id = Column(Integer, primary_key=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SendLog(Base):
    __tablename__ = "send_log"
    id = Column(Integer, primary_key=True)
    food = Column(Text, default="")
    location = Column(String(200), default="")
    room = Column(String(100), default="")
    end_time = Column(String(100), default="")
    notes = Column(Text, default="")
    sent = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    total = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)


def replace_subscribers(rows: list[dict]) -> int:
    """
    Replace the whole subscriber list with `rows` (dicts with 'name'/'email').
    Duplicate emails within the upload are collapsed. Returns rows imported.
    """
    deduped = {}
    for row in rows:
        email = (row.get("email") or "").strip().lower()
        if email and "@" in email:
            deduped[email] = (row.get("name") or "").strip()

    with Session(engine) as session:
        session.query(Subscriber).delete()
        for email, name in deduped.items():
            session.add(Subscriber(email=email, name=name))
        session.commit()
    return len(deduped)


def get_active_subscribers() -> list[dict]:
    """All subscribers minus anyone on the suppression list."""
    with Session(engine) as session:
        suppressed = {s.email for s in session.scalars(select(Suppression))}
        return [
            {"name": s.name, "email": s.email}
            for s in session.scalars(select(Subscriber).order_by(Subscriber.email))
            if s.email not in suppressed
        ]


def subscriber_count() -> int:
    with Session(engine) as session:
        return session.query(Subscriber).count()


def suppressed_count() -> int:
    with Session(engine) as session:
        return session.query(Suppression).count()


def suppress_email(email: str):
    """Add an email to the permanent suppression list (idempotent)."""
    email = email.strip().lower()
    with Session(engine) as session:
        exists = session.scalar(select(Suppression).where(Suppression.email == email))
        if not exists:
            session.add(Suppression(email=email))
            session.commit()


def is_suppressed(email: str) -> bool:
    with Session(engine) as session:
        return session.scalar(
            select(Suppression).where(Suppression.email == email.strip().lower())
        ) is not None


def log_send(food, location, room, end_time, notes, sent, failed, total):
    with Session(engine) as session:
        session.add(SendLog(
            food=food, location=location, room=room, end_time=end_time,
            notes=notes, sent=sent, failed=failed, total=total,
        ))
        session.commit()


def get_send_logs(limit: int = 100) -> list[dict]:
    with Session(engine) as session:
        logs = session.scalars(
            select(SendLog).order_by(SendLog.created_at.desc()).limit(limit)
        )
        return [
            {
                "food": l.food, "location": l.location, "room": l.room,
                "end_time": l.end_time, "notes": l.notes,
                "sent": l.sent, "failed": l.failed, "total": l.total,
                "created_at": l.created_at,
            }
            for l in logs
        ]
