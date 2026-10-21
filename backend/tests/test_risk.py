from app.schemas.security import ToolRequest
from app.services.risk.engine import RiskEngine


def test_high_risk_transfer():
    engine = RiskEngine()

    request = ToolRequest(
        agent_id=1,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 80000,
            "vendor_verified": False,
        },
    )

    result = engine.assess(request)

    assert result.score == 100
    assert "High-value financial transaction" in result.reasons
    assert "Recipient is new" in result.reasons
    assert "Vendor has not been verified" in result.reasons


def test_low_risk_transfer():
    engine = RiskEngine()

    request = ToolRequest(
        agent_id=1,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    result = engine.assess(request)

    assert result.score == 0
    assert result.reasons == []


def test_medium_risk_transfer():
    engine = RiskEngine()

    request = ToolRequest(
        agent_id=1,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    result = engine.assess(request)

    assert result.score == 30
    assert result.reasons == ["Recipient is new"]

def test_disallowed_tool_increases_risk(db_session):
    from app.models.agent import Agent

    agent = Agent(
        name="Restricted Agent",
        allowed_tools=["send_email"],
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    assessment = RiskEngine().assess(
        request=request,
        db=db_session,
    )

    assert assessment.score == 60
    assert "Tool is not permitted for this agent" in assessment.reasons

def test_allowed_tool_does_not_add_permission_risk():
    request = ToolRequest(
        agent_id=1,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
        allowed_tools=["transfer_money"],
    )

    assessment = RiskEngine().assess(request)

    assert assessment.score == 0
    assert assessment.reasons == []