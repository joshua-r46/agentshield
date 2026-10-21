import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.session import Base
from app.models.agent import Agent
from app.models.agent_action import AgentAction
from app.models.security_event import SecurityEvent
from app.models.user import User


TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()