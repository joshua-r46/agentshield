from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id"),
        nullable=False,
        index=True,
    )

    tool: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    arguments: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    risk_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    decision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )