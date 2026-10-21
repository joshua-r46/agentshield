from app.models.agent import Agent
from app.services.verification.trace_service import ExecutionTraceService


def create_test_agent(db_session):
    agent = Agent(
        name="Trace Test Agent",
        description="Agent used for execution trace tests",
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    return agent


def test_record_execution(db_session):
    agent = create_test_agent(db_session)

    service = ExecutionTraceService()

    trace = service.record_execution(
        db=db_session,
        agent_id=agent.id,
        tool="verify_vendor",
        arguments={
            "vendor": "new_vendor",
        },
        execution_status="SUCCESS",
        result={
            "verified": True,
        },
    )

    assert trace.id is not None
    assert trace.agent_id == agent.id
    assert trace.tool == "verify_vendor"
    assert trace.arguments["vendor"] == "new_vendor"
    assert trace.execution_status == "SUCCESS"
    assert trace.result["verified"] is True


def test_get_trace(db_session):
    agent = create_test_agent(db_session)

    service = ExecutionTraceService()

    created = service.record_execution(
        db=db_session,
        agent_id=agent.id,
        tool="verify_vendor",
        arguments={
            "vendor": "new_vendor",
        },
        execution_status="SUCCESS",
        result={
            "verified": True,
        },
    )

    trace = service.get_trace(
        db=db_session,
        trace_id=created.id,
    )

    assert trace.id == created.id
    assert trace.tool == "verify_vendor"


def test_get_missing_trace_raises_error(db_session):
    service = ExecutionTraceService()

    try:
        service.get_trace(
            db=db_session,
            trace_id=999999,
        )
    except ValueError as exc:
        assert str(exc) == "Execution trace not found"
    else:
        raise AssertionError("Expected ValueError")