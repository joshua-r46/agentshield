from app.models.agent import Agent
from app.schemas.security import ToolRequest
from app.services.security.anomaly import BehavioralAnomalyEngine
from app.services.verification.trace_service import ExecutionTraceService


def create_test_agent(db_session):
    agent = Agent(
        name="Anomaly Test Agent",
        description="Agent used for anomaly detection tests",
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    return agent


def test_known_tool_is_not_anomalous(db_session):
    agent = create_test_agent(db_session)

    trace_service = ExecutionTraceService()
    engine = BehavioralAnomalyEngine()

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

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": 2000,
        },
    )

    assessment = engine.assess(
        db=db_session,
        request=request,
    )

    assert assessment.score == 0
    assert assessment.reasons == []


def test_unknown_tool_is_anomalous(db_session):
    agent = create_test_agent(db_session)

    engine = BehavioralAnomalyEngine()

    request = ToolRequest(
        agent_id=agent.id,
        tool="delete_customer",
        arguments={
            "customer_id": 123,
        },
    )

    assessment = engine.assess(
        db=db_session,
        request=request,
    )

    assert assessment.score == 40
    assert "Tool is unusual for this agent" in assessment.reasons


def test_unusually_high_transfer_is_anomalous(db_session):
    agent = create_test_agent(db_session)

    trace_service = ExecutionTraceService()
    engine = BehavioralAnomalyEngine()

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

    trace_service.record_execution(
        db=db_session,
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "another_vendor",
            "amount": 2000,
        },
        execution_status="SUCCESS",
        result={
            "success": True,
        },
    )

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 5000,
        },
    )

    assessment = engine.assess(
        db=db_session,
        request=request,
    )

    assert assessment.score == 40
    assert "Transfer amount is unusually high for this agent" in assessment.reasons


def test_anomaly_score_is_capped_at_100(db_session):
    agent = create_test_agent(db_session)

    engine = BehavioralAnomalyEngine()

    request = ToolRequest(
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 80000,
        },
    )

    assessment = engine.assess(
        db=db_session,
        request=request,
    )

    assert 0 <= assessment.score <= 100