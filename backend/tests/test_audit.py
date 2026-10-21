from app.models.agent import Agent
from app.schemas.security import SecurityDecision, ToolRequest
from app.services.audit.service import AuditService


def test_audit_service_logs_security_decision(db_session):
    agent = Agent(
        name="Test Agent",
        description="Audit test agent",
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 80000,
            "vendor_verified": False,
        },
    )

    decision = SecurityDecision(
        decision="BLOCK",
        risk_score=100,
        reasons=[
            "High-value financial transaction",
            "Recipient is new",
            "Vendor has not been verified",
        ],
    )

    service = AuditService()

    event = service.log_security_decision(
        db=db_session,
        request=request,
        decision=decision,
        message="High-risk transfer blocked",
    )

    assert event.id is not None
    assert event.agent_id == agent.id
    assert event.tool == "transfer_money"
    assert event.risk_score == 100
    assert event.decision == "BLOCK"
    assert event.event_type == "SECURITY_DECISION"
    assert event.message == "High-risk transfer blocked"