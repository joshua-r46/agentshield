from app.models.agent import Agent
from app.services.agent.runner import AgentRunner
from app.services.policy.engine import PolicyEngine
from app.services.security.enforcement import (
    SecureToolExecutor,
    ToolExecutionBlocked,
)
from app.services.security.interceptor import AgentShieldInterceptor
from app.services.security.service import AgentShieldService
from app.services.tools.registry import ToolRegistry


def create_runner(db_session):
    agent = Agent(
        name="Runner Test Agent",
        description="AgentRunner test agent",
        allowed_tools=["transfer_money"],
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    registry = ToolRegistry()

    calls = []

    def fake_transfer_money(recipient, amount):
        calls.append(
            {
                "recipient": recipient,
                "amount": amount,
            }
        )

        return {
            "success": True,
            "message": "Transfer completed",
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

    security_service = AgentShieldService(
        interceptor=interceptor,
        registry=registry,
        policy_engine=policy_engine,
        executor=executor,
    )

    runner = AgentRunner(
        security_service=security_service,
    )

    return runner, agent.id, calls


def test_agent_runner_executes_safe_action(db_session):
    runner, agent_id, calls = create_runner(db_session)

    decision, result = runner.execute_action(
        db=db_session,
        agent_id=agent_id,
        tool="transfer_money",
        arguments={
            "recipient": "existing_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    assert decision.decision == "ALLOW"
    assert result["success"] is True

    assert len(calls) == 1


def test_agent_runner_blocks_high_risk_action(db_session):
    runner, agent_id, calls = create_runner(db_session)

    try:
        runner.execute_action(
            db=db_session,
            agent_id=agent_id,
            tool="transfer_money",
            arguments={
                "recipient": "new_vendor",
                "amount": 80000,
                "vendor_verified": False,
            },
        )

        assert False, "Expected ToolExecutionBlocked"

    except ToolExecutionBlocked as exc:
        assert exc.decision.decision == "BLOCK"
        assert exc.decision.risk_score == 100

    assert len(calls) == 0


def test_agent_runner_propose_action_does_not_execute_tool(db_session):
    runner, agent_id, calls = create_runner(db_session)

    decision = runner.propose_action(
        db=db_session,
        agent_id=agent_id,
        tool="transfer_money",
        arguments={
            "recipient": "existing_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    assert decision.decision == "ALLOW"

    assert len(calls) == 0
def test_agent_runner_executes_plan(db_session):
    runner, agent_id, calls = create_runner(db_session)

    result = runner.execute_plan(
        db=db_session,
        agent_id=agent_id,
        actions=[
            {
                "tool": "transfer_money",
                "arguments": {
                    "recipient": "existing_vendor",
                    "amount": 1000,
                    "vendor_verified": True,
                },
            }
        ],
    )

    assert result["status"] == "COMPLETED"
    assert len(result["completed_actions"]) == 1

    completed_action = result["completed_actions"][0]

    assert completed_action["tool"] == "transfer_money"

    decision, tool_result = completed_action["result"]

    assert decision.decision == "ALLOW"
    assert tool_result["success"] is True

    assert len(calls) == 1


def test_agent_runner_stops_when_action_is_blocked(db_session):
    runner, agent_id, calls = create_runner(db_session)

    try:
        runner.execute_plan(
            db=db_session,
            agent_id=agent_id,
            actions=[
                {
                    "tool": "transfer_money",
                    "arguments": {
                        "recipient": "new_vendor",
                        "amount": 80000,
                        "vendor_verified": False,
                    },
                },
                {
                    "tool": "transfer_money",
                    "arguments": {
                        "recipient": "existing_vendor",
                        "amount": 1000,
                        "vendor_verified": True,
                    },
                },
            ],
        )

        assert False, "Expected ToolExecutionBlocked"

    except ToolExecutionBlocked as exc:
        assert exc.decision.decision == "BLOCK"

    # Neither action should reach the fake tool because the first
    # action is blocked.
    assert len(calls) == 0    

def test_agent_runner_pauses_plan_for_approval(db_session):
    runner, agent_id, calls = create_runner(db_session)

    result = runner.execute_plan(
        db=db_session,
        agent_id=agent_id,
        actions=[
            {
                "tool": "transfer_money",
                "arguments": {
                    "recipient": "new_vendor",
                    "amount": 10000,
                    "vendor_verified": False,
                },
            },
            {
                "tool": "transfer_money",
                "arguments": {
                    "recipient": "existing_vendor",
                    "amount": 1000,
                    "vendor_verified": True,
                },
            },
        ],
    )

    assert result["status"] == "REQUIRES_APPROVAL"
    assert result["approval_id"] is not None
    assert result["completed_actions"] == []

    # The action requiring approval must not execute.
    # The next action must not execute either.
    assert len(calls) == 0


def test_agent_runner_completes_plan_when_all_actions_allowed(db_session):
    runner, agent_id, calls = create_runner(db_session)

    result = runner.execute_plan(
        db=db_session,
        agent_id=agent_id,
        actions=[
            {
                "tool": "transfer_money",
                "arguments": {
                    "recipient": "existing_vendor",
                    "amount": 1000,
                    "vendor_verified": True,
                },
            },
        ],
    )

    assert result["status"] == "COMPLETED"
    assert len(result["completed_actions"]) == 1
    assert result["completed_actions"][0]["tool"] == "transfer_money"

    assert len(calls) == 1