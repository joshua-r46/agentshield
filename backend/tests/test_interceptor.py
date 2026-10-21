import pytest

from app.models.agent import Agent
from app.services.verification.trace_service import ExecutionTraceService
from app.models.agent import Agent
from app.schemas.security import ToolRequest
from app.services.policy.engine import PolicyEngine
from app.services.security.enforcement import (
    SecureToolExecutor,
    ToolExecutionBlocked,
)
from app.services.security.interceptor import AgentShieldInterceptor
from app.services.tools.fake_bank import FakeBankAPI
from app.services.tools.registry import ToolRegistry


def create_test_agent(db_session):
    agent = Agent(
    name="Strong Anomaly Agent",
    description="Test agent",
    allowed_tools=["transfer_money"],
)

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    return agent


def create_executor() -> SecureToolExecutor:
    interceptor = AgentShieldInterceptor()
    registry = ToolRegistry()

    bank = FakeBankAPI()
    registry.register("transfer_money", bank.transfer_money)

    return SecureToolExecutor(
        interceptor,
        registry,
        PolicyEngine(),
    )


def test_high_risk_transfer_is_blocked(db_session):
    agent = create_test_agent(db_session)
    executor = create_executor()

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 80000,
            "vendor_verified": False,
        },
    )

    with pytest.raises(ToolExecutionBlocked) as exc_info:
        executor.execute(request, db_session)

    assert exc_info.value.decision.decision == "BLOCK"
    assert exc_info.value.decision.risk_score == 100


def test_low_risk_action_is_allowed(db_session):
    agent = create_test_agent(db_session)
    executor = create_executor()

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    decision, result = executor.execute(request, db_session)

    assert decision.decision == "ALLOW"
    assert decision.risk_score == 0
    assert result.success is True


def test_blocked_action_never_reaches_tool(db_session):
    agent = create_test_agent(db_session)
    interceptor = AgentShieldInterceptor()
    registry = ToolRegistry()

    tool_called = False

    def monitored_transfer(**kwargs):
        nonlocal tool_called
        tool_called = True
        return {"success": True}

    registry.register("transfer_money", monitored_transfer)

    executor = SecureToolExecutor(
        interceptor,
        registry,
        PolicyEngine(),
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
        executor.execute(request, db_session)

    assert tool_called is False


def test_allowed_action_reaches_registered_tool(db_session):
    agent = create_test_agent(db_session)
    interceptor = AgentShieldInterceptor()
    registry = ToolRegistry()

    tool_called = False

    def monitored_transfer(**kwargs):
        nonlocal tool_called
        tool_called = True
        return {"success": True}

    registry.register("transfer_money", monitored_transfer)

    executor = SecureToolExecutor(
        interceptor,
        registry,
        PolicyEngine(),
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

    decision, result = executor.execute(request, db_session)

    assert decision.decision == "ALLOW"
    assert tool_called is True
    assert result == {"success": True}


def test_unregistered_tool_is_not_executed(db_session):
    agent = create_test_agent(db_session)
    executor = create_executor()

    request = ToolRequest(
        agent_id=agent.id,
        tool="delete_database",
        arguments={},
    )

    with pytest.raises(Exception):
        executor.execute(request, db_session)


def test_policy_violation_is_blocked_before_tool_execution(db_session):
    agent = create_test_agent(db_session)
    interceptor = AgentShieldInterceptor()
    registry = ToolRegistry()

    tool_called = False

    def monitored_transfer(**kwargs):
        nonlocal tool_called
        tool_called = True
        return {"success": True}

    registry.register("transfer_money", monitored_transfer)

    executor = SecureToolExecutor(
        interceptor,
        registry,
        PolicyEngine(),
    )

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "blocked_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    with pytest.raises(ToolExecutionBlocked) as exc_info:
        executor.execute(request, db_session)

    assert exc_info.value.decision.decision == "BLOCK"
    assert exc_info.value.decision.risk_score == 100
    assert "Recipient is blocked" in exc_info.value.decision.reasons
    assert tool_called is False

def test_interceptor_includes_behavioral_anomaly_reason(db_session):
    agent = Agent(
        name="Anomaly Interceptor Agent",
        description="Test agent",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    trace_service = ExecutionTraceService()

    trace_service.record_execution(
        db=db_session,
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": 1000,
        },
        execution_status="SUCCESS",
        result={
            "success": True,
        },
    )

    interceptor = AgentShieldInterceptor()

    request = ToolRequest(
        agent_id=agent.id,
        tool="delete_customer",
        arguments={
            "customer_id": 123,
        },
    )

    decision = interceptor.evaluate(
        request=request,
        db=db_session,
    )

    assert "Tool is unusual for this agent" in decision.reasons

def test_strong_behavioral_anomaly_increases_security_score(db_session):
    agent = Agent(
        name="Strong Anomaly Agent",
        description="Test agent",
        allowed_tools=["transfer_money"],
)
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    trace_service = ExecutionTraceService()

    trace_service.record_execution(
        db=db_session,
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": 1000,
        },
        execution_status="SUCCESS",
        result={
            "success": True,
        },
    )

    interceptor = AgentShieldInterceptor()

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 5000,
        },
    )

    decision = interceptor.evaluate(
        request=request,
        db=db_session,
    )

    assert decision.risk_score == 50
    assert "Transfer amount is unusually high for this agent" in decision.reasons