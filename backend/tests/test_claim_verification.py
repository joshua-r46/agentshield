from app.models.agent import Agent
from app.services.verification.claim_service import ClaimService
from app.services.verification.trace_service import ExecutionTraceService
from app.services.verification.verifier import ClaimVerificationService


def create_test_agent(db_session):
    agent = Agent(
        name="Verification Test Agent",
        description="Agent used for claim verification tests",
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    return agent


def test_claim_is_verified_when_matching_trace_exists(db_session):
    agent = create_test_agent(db_session)

    claim_service = ClaimService()
    trace_service = ExecutionTraceService()
    verifier = ClaimVerificationService()

    claim = claim_service.create_claim(
        db=db_session,
        agent_id=agent.id,
        claim_type="TOOL_EXECUTION",
        claim_text="Vendor verification completed",
        claimed_tool="verify_vendor",
        claimed_arguments={
            "vendor": "new_vendor",
        },
    )

    trace_service.record_execution(
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

    verified_claim = verifier.verify_claim(
        db=db_session,
        claim_id=claim.id,
    )

    assert verified_claim.verification_status == "VERIFIED"


def test_claim_is_mismatch_when_tool_was_not_executed(db_session):
    agent = create_test_agent(db_session)

    claim_service = ClaimService()
    trace_service = ExecutionTraceService()
    verifier = ClaimVerificationService()

    claim = claim_service.create_claim(
        db=db_session,
        agent_id=agent.id,
        claim_type="TOOL_EXECUTION",
        claim_text="Vendor verification completed",
        claimed_tool="verify_vendor",
        claimed_arguments={
            "vendor": "new_vendor",
        },
    )

    trace_service.record_execution(
        db=db_session,
        agent_id=agent.id,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 80000,
        },
        execution_status="SUCCESS",
        result={
            "success": True,
        },
    )

    verified_claim = verifier.verify_claim(
        db=db_session,
        claim_id=claim.id,
    )

    assert verified_claim.verification_status == "MISMATCH"


def test_claim_is_mismatch_when_arguments_do_not_match(db_session):
    agent = create_test_agent(db_session)

    claim_service = ClaimService()
    trace_service = ExecutionTraceService()
    verifier = ClaimVerificationService()

    claim = claim_service.create_claim(
        db=db_session,
        agent_id=agent.id,
        claim_type="TOOL_EXECUTION",
        claim_text="Vendor verification completed",
        claimed_tool="verify_vendor",
        claimed_arguments={
            "vendor": "trusted_vendor",
        },
    )

    trace_service.record_execution(
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

    verified_claim = verifier.verify_claim(
        db=db_session,
        claim_id=claim.id,
    )

    assert verified_claim.verification_status == "MISMATCH"


def test_failed_execution_does_not_verify_claim(db_session):
    agent = create_test_agent(db_session)

    claim_service = ClaimService()
    trace_service = ExecutionTraceService()
    verifier = ClaimVerificationService()

    claim = claim_service.create_claim(
        db=db_session,
        agent_id=agent.id,
        claim_type="TOOL_EXECUTION",
        claim_text="Vendor verification completed",
        claimed_tool="verify_vendor",
        claimed_arguments={
            "vendor": "new_vendor",
        },
    )

    trace_service.record_execution(
        db=db_session,
        agent_id=agent.id,
        tool="verify_vendor",
        arguments={
            "vendor": "new_vendor",
        },
        execution_status="FAILED",
        result={
            "error": "Verification service unavailable",
        },
    )

    verified_claim = verifier.verify_claim(
        db=db_session,
        claim_id=claim.id,
    )

    assert verified_claim.verification_status == "MISMATCH"