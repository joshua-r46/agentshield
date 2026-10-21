from app.models.agent import Agent
from app.schemas.security import SecurityDecision, ToolRequest
from app.services.approval.service import ApprovalService


def create_test_agent(db_session) -> Agent:
    agent = Agent(
        name="Approval Test Agent",
        description="Agent used for approval tests",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


def test_create_approval(db_session):
    agent = create_test_agent(db_session)

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 40000,
        },
    )

    decision = SecurityDecision(
        decision="REQUIRE_APPROVAL",
        risk_score=50,
        reasons=["Medium-risk financial transaction"],
    )

    service = ApprovalService()

    approval = service.create_approval(
        db=db_session,
        request=request,
        decision=decision,
    )

    assert approval.id is not None
    assert approval.agent_id == agent.id
    assert approval.tool == "transfer_money"
    assert approval.risk_score == 50
    assert approval.status == "PENDING"


def test_approve_request(db_session):
    agent = create_test_agent(db_session)

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 40000,
        },
    )

    decision = SecurityDecision(
        decision="REQUIRE_APPROVAL",
        risk_score=50,
        reasons=["Medium-risk financial transaction"],
    )

    service = ApprovalService()

    approval = service.create_approval(
        db=db_session,
        request=request,
        decision=decision,
    )

    approved = service.approve(
        db=db_session,
        approval_id=approval.id,
        reviewed_by="admin",
    )

    assert approved.status == "APPROVED"
    assert approved.reviewed_by == "admin"
    assert approved.reviewed_at is not None


def test_reject_request(db_session):
    agent = create_test_agent(db_session)

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 40000,
        },
    )

    decision = SecurityDecision(
        decision="REQUIRE_APPROVAL",
        risk_score=50,
        reasons=["Medium-risk financial transaction"],
    )

    service = ApprovalService()

    approval = service.create_approval(
        db=db_session,
        request=request,
        decision=decision,
    )

    rejected = service.reject(
        db=db_session,
        approval_id=approval.id,
        reviewed_by="admin",
    )

    assert rejected.status == "REJECTED"
    assert rejected.reviewed_by == "admin"
    assert rejected.reviewed_at is not None


def test_cannot_approve_already_rejected_request(db_session):
    agent = create_test_agent(db_session)

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 40000,
        },
    )

    decision = SecurityDecision(
        decision="REQUIRE_APPROVAL",
        risk_score=50,
        reasons=["Medium-risk financial transaction"],
    )

    service = ApprovalService()

    approval = service.create_approval(
        db=db_session,
        request=request,
        decision=decision,
    )

    service.reject(
        db=db_session,
        approval_id=approval.id,
        reviewed_by="admin",
    )

    try:
        service.approve(
            db=db_session,
            approval_id=approval.id,
            reviewed_by="admin",
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "already REJECTED" in str(exc)

def test_build_tool_request(db_session):
    agent = create_test_agent(db_session)

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 40000,
        },
    )

    decision = SecurityDecision(
        decision="REQUIRE_APPROVAL",
        risk_score=50,
        reasons=["Medium-risk financial transaction"],
    )

    service = ApprovalService()

    approval = service.create_approval(
        db=db_session,
        request=request,
        decision=decision,
    )

    rebuilt_request = service.build_tool_request(approval)

    assert rebuilt_request.agent_id == request.agent_id
    assert rebuilt_request.tool == request.tool
    assert rebuilt_request.arguments == request.arguments