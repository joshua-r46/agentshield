from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class AgentClaim(Base):
    __tablename__ = "agent_claims"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id"),
        nullable=False,
        index=True,
    )

    claim_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    claim_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    claimed_tool: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    claimed_arguments: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    verification_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )