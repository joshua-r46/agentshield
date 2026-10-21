import pytest

from app.models.agent import Agent
from app.services.security.permissions import AgentPermissionService


def test_get_allowed_tools(db_session):
    agent = Agent(
        name="Finance Agent",
        allowed_tools=["transfer_money", "send_email"],
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    service = AgentPermissionService()

    tools = service.get_allowed_tools(
        db=db_session,
        agent_id=agent.id,
    )

    assert tools == ["transfer_money", "send_email"]


def test_unknown_agent_raises_error(db_session):
    service = AgentPermissionService()

    with pytest.raises(ValueError, match="Agent not found"):
        service.get_allowed_tools(
            db=db_session,
            agent_id=9999,
        )


def test_inactive_agent_raises_error(db_session):
    agent = Agent(
        name="Inactive Agent",
        allowed_tools=["transfer_money"],
        is_active=False,
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    service = AgentPermissionService()

    with pytest.raises(ValueError, match="Agent is inactive"):
        service.get_allowed_tools(
            db=db_session,
            agent_id=agent.id,
        )