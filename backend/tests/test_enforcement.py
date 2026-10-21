import pytest

from app.models.agent import Agent
from app.models.approval import Approval
from app.models.execution_trace import ExecutionTrace
from app.schemas.security import SecurityDecision, ToolRequest
from app.services.approval.service import ApprovalService
from app.services.policy.engine import PolicyEngine
from app.services.risk.engine import RiskAssessment
from app.services.security.enforcement import (
    SecureToolExecutor,
    ToolExecutionBlocked,
)
from app.services.security.interceptor import AgentShieldInterceptor
from app.services.tools.registry import ToolRegistry


class MediumRiskEngine:
    def assess(self, request, db=None):
        return RiskAssessment(
            score=50,
            reasons=["Medium-risk action"],
        )


class RevalidationRiskEngine:
    def assess(self, request, db=None):
        return RiskAssessment(
            score=10,
            reasons=["Low-risk after revalidation"],
        )


def create_test_agent(db_session):
    agent = Agent(
        name="Test Agent",
        description="Enforcement test agent",
        allowed_tools=["transfer_money"],
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    return agent


def create_executor(db_session, risk_engine=None):
    registry = ToolRegistry()

    def fake_transfer_money(
        recipient: str,
        amount: float,
    ):
        return {
            "success": True,
            "recipient": recipient,
            "amount": amount,
        }

    registry.register(
        "transfer_money",
        fake_transfer_money,
    )

    return SecureToolExecutor(
        interceptor=(
            AgentShieldInterceptor(
                risk_engine=risk_engine,
            )
            if risk_engine
            else AgentShieldInterceptor()
        ),
        registry=registry,
        policy_engine=PolicyEngine(),
    )


def test_high_risk_action_is_blocked_and_logged(db_session):
    agent = create_test_agent(db_session)

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 80000,
            "vendor_verified": False,
        },
    )

    executor = create_executor(db_session)

    with pytest.raises(ToolExecutionBlocked) as exc_info:
        executor.execute(
            request=request,
            db=db_session,
        )

    decision = exc_info.value.decision

    assert decision.decision == "BLOCK"
    assert decision.risk_score >= 71

    from app.models.security_event import SecurityEvent

    event = (
        db_session.query(SecurityEvent)
        .filter_by(agent_id=agent.id)
        .first()
    )

    assert event is not None
    assert event.tool == "transfer_money"
    assert event.decision == "BLOCK"


def test_allowed_action_is_logged(db_session):
    agent = create_test_agent(db_session)

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    executor = create_executor(db_session)

    decision, result = executor.execute(
        request=request,
        db=db_session,
    )

    assert decision.decision == "ALLOW"
    assert result["success"] is True
    assert result["recipient"] == "trusted_vendor"
    assert result["amount"] == 1000

    from app.models.security_event import SecurityEvent

    event = (
        db_session.query(SecurityEvent)
        .filter_by(agent_id=agent.id)
        .first()
    )

    assert event is not None
    assert event.tool == "transfer_money"
    assert event.decision == "ALLOW"


def test_require_approval_creates_pending_approval_and_blocks_tool(
    db_session,
):
    agent = create_test_agent(db_session)

    tool_called = False

    def fake_transfer_money(
        recipient: str,
        amount: float,
    ):
        nonlocal tool_called
        tool_called = True

        return {
            "success": True,
            "recipient": recipient,
            "amount": amount,
        }

    registry = ToolRegistry()

    registry.register(
        "transfer_money",
        fake_transfer_money,
    )

    executor = SecureToolExecutor(
        interceptor=AgentShieldInterceptor(
            risk_engine=MediumRiskEngine(),
        ),
        registry=registry,
        policy_engine=PolicyEngine(),
    )

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    with pytest.raises(ToolExecutionBlocked) as exc_info:
        executor.execute(
            request=request,
            db=db_session,
        )

    decision = exc_info.value.decision

    assert decision.decision == "REQUIRE_APPROVAL"
    assert decision.risk_score == 50
    assert exc_info.value.approval_id is not None

    approval_id = exc_info.value.approval_id

    # The actual tool must NEVER execute before approval.
    assert tool_called is False

    approval = db_session.get(
        Approval,
        approval_id,
    )

    assert approval is not None
    assert approval.status == "PENDING"
    assert approval.agent_id == agent.id
    assert approval.tool == "transfer_money"
    assert approval.risk_score == 50


def test_approved_action_executes_after_revalidation(db_session):
    agent = create_test_agent(db_session)

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 10000,
            "vendor_verified": False,
        },
    )

    interceptor = AgentShieldInterceptor(
        risk_engine=RevalidationRiskEngine(),
    )

    registry = ToolRegistry()

    called = {
        "value": False,
    }

    def fake_transfer(
        recipient,
        amount,
    ):
        called["value"] = True

        return {
            "success": True,
            "recipient": recipient,
            "amount": amount,
        }

    registry.register(
        "transfer_money",
        fake_transfer,
    )

    executor = SecureToolExecutor(
        interceptor=interceptor,
        registry=registry,
        policy_engine=PolicyEngine(),
    )

    approval = ApprovalService().create_approval(
        db=db_session,
        request=request,
        decision=SecurityDecision(
            decision="REQUIRE_APPROVAL",
            risk_score=50,
            reasons=["Medium-risk action"],
        ),
    )

    ApprovalService().approve(
        db=db_session,
        approval_id=approval.id,
        reviewed_by="admin",
    )

    decision, result = executor.execute_approved(
        approval_id=approval.id,
        db=db_session,
    )

    assert decision.decision == "ALLOW"
    assert called["value"] is True
    assert result["success"] is True


def test_allowed_execution_creates_success_trace(db_session):
    agent = create_test_agent(db_session)

    calls = []

    def fake_tool(
        recipient: str,
        amount: float,
    ):
        calls.append(
            (
                recipient,
                amount,
            )
        )

        return {
            "success": True,
            "transaction_id": "TX-TRACE-001",
        }

    registry = ToolRegistry()

    registry.register(
        "transfer_money",
        fake_tool,
    )

    executor = SecureToolExecutor(
        interceptor=AgentShieldInterceptor(),
        registry=registry,
        policy_engine=PolicyEngine(),
    )

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    decision, result = executor.execute(
        request=request,
        db=db_session,
    )

    assert decision.decision == "ALLOW"
    assert result["success"] is True

    # vendor_verified is security metadata and must NOT
    # reach the actual tool.
    assert calls == [
        (
            "trusted_vendor",
            1000,
        )
    ]

    traces = (
        db_session
        .query(ExecutionTrace)
        .all()
    )

    assert len(traces) == 1
    assert traces[0].tool == "transfer_money"
    assert traces[0].execution_status == "SUCCESS"
    assert traces[0].result["success"] is True


def test_blocked_execution_creates_no_execution_trace(db_session):
    agent = create_test_agent(db_session)

    calls = []

    def fake_tool(
        recipient: str,
        amount: float,
    ):
        calls.append(True)

        return {
            "success": True,
        }

    registry = ToolRegistry()

    registry.register(
        "transfer_money",
        fake_tool,
    )

    executor = SecureToolExecutor(
        interceptor=AgentShieldInterceptor(),
        registry=registry,
        policy_engine=PolicyEngine(),
    )

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 80000,
            "vendor_verified": False,
        },
    )

    with pytest.raises(ToolExecutionBlocked):
        executor.execute(
            request=request,
            db=db_session,
        )

    # Dangerous tool was never reached.
    assert calls == []

    traces = (
        db_session
        .query(ExecutionTrace)
        .all()
    )

    assert traces == []