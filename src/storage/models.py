"""SQLAlchemy models for ScholarRank database."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Scholarship(Base):
    """Core scholarship table storing scraped scholarship data."""

    __tablename__ = "scholarships"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    amount_min: Mapped[Optional[int]] = mapped_column(Integer)  # In cents
    amount_max: Mapped[Optional[int]] = mapped_column(Integer)  # In cents
    deadline: Mapped[Optional[datetime]] = mapped_column(Date, index=True)
    application_url: Mapped[Optional[str]] = mapped_column(Text)
    raw_eligibility: Mapped[Optional[str]] = mapped_column(Text)
    parsed_eligibility: Mapped[Optional[dict]] = mapped_column(JSON)
    effort_score: Mapped[Optional[int]] = mapped_column(Integer)  # 1-10
    competition_score: Mapped[Optional[int]] = mapped_column(Integer)  # 1-10
    is_renewable: Mapped[Optional[bool]] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_source_source_id"),
    )

    def __repr__(self) -> str:
        return f"<Scholarship(id={self.id!r}, title={self.title!r}, source={self.source!r})>"


class FetchLog(Base):
    """Fetch history for tracking incremental updates."""

    __tablename__ = "fetch_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    scholarships_found: Mapped[Optional[int]] = mapped_column(Integer)
    scholarships_new: Mapped[Optional[int]] = mapped_column(Integer)
    errors: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<FetchLog(id={self.id}, source={self.source!r}, fetched_at={self.fetched_at})>"
