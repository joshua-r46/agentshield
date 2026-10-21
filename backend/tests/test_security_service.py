from app.models.agent import Agent
from app.schemas.security import ToolRequest
from app.services.policy.engine import PolicyEngine
from app.services.security.enforcement import SecureToolExecutor
from app.services.security.interceptor import AgentShieldInterceptor
from app.services.security.service import AgentShieldService
from app.services.tools.registry import ToolRegistry


def create_service():
    interceptor = AgentShieldInterceptor()
    registry = ToolRegistry()
    policy_engine = PolicyEngine()

    executor = SecureToolExecutor(
        interceptor=interceptor,
        registry=registry,
        policy_engine=policy_engine,
    )

    return AgentShieldService(
        interceptor=interceptor,
        registry=registry,
        policy_engine=policy_engine,
        executor=executor,
    )


def test_safe_action_is_allowed(db_session):
    agent = Agent(
        name="Safe Agent",
        allowed_tools=["transfer_money"],
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    service = create_service()

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    decision = service.evaluate(
        request=request,
        db=db_session,
    )

    assert decision.decision == "ALLOW"


def test_unpermitted_tool_is_high_risk(db_session):
    agent = Agent(
        name="Restricted Agent",
        allowed_tools=["send_email"],
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    service = create_service()

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    decision = service.evaluate(
        request=request,
        db=db_session,
    )

    assert decision.risk_score == 60
    assert "Tool is not permitted for this agent" in decision.reasons

def test_execution_goes_through_secure_executor(db_session):
    agent = Agent(
        name="Execution Agent",
        allowed_tools=["transfer_money"],
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    registry = ToolRegistry()

    called = {"value": False}

    def fake_transfer_money(recipient: str, amount: float):
        called["value"] = True
        return {
            "success": True,
            "recipient": recipient,
            "amount": amount,
        }

    registry.register(
        "transfer_money",
        fake_transfer_money,
    )

    interceptor = AgentShieldInterceptor()
    policy_engine = PolicyEngine()

    executor = SecureToolExecutor(
        interceptor=interceptor,
        registry=registry,
        policy_engine=policy_engine,
    )

    service = AgentShieldService(
        interceptor=interceptor,
        registry=registry,
        policy_engine=policy_engine,
        executor=executor,
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

    decision, result = service.execute(
        request=request,
        db=db_session,
    )

    assert decision.decision == "ALLOW"
    assert result["success"] is True
    assert called["value"] is True