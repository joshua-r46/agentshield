from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class ExecutionTrace(Base):
    __tablename__ = "execution_traces"

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

    tool: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    arguments: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    execution_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )