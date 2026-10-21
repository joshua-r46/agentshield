from app.models.agent import Agent
from app.services.verification.claim_service import ClaimService


def create_test_agent(db_session):
    agent = Agent(
        name="Claim Test Agent",
        description="Agent used for claim verification tests",
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    return agent


def test_create_claim(db_session):
    agent = create_test_agent(db_session)

    service = ClaimService()

    claim = service.create_claim(
        db=db_session,
        agent_id=agent.id,
        claim_type="TOOL_EXECUTION",
        claim_text="Vendor verification completed",
        claimed_tool="verify_vendor",
        claimed_arguments={
            "vendor": "new_vendor",
        },
    )

    assert claim.id is not None
    assert claim.agent_id == agent.id
    assert claim.claim_type == "TOOL_EXECUTION"
    assert claim.claim_text == "Vendor verification completed"
    assert claim.claimed_tool == "verify_vendor"
    assert claim.verification_status == "PENDING"


def test_get_claim(db_session):
    agent = create_test_agent(db_session)

    service = ClaimService()

    created = service.create_claim(
        db=db_session,
        agent_id=agent.id,
        claim_type="TOOL_EXECUTION",
        claim_text="Vendor verification completed",
        claimed_tool="verify_vendor",
    )

    claim = service.get_claim(
        db=db_session,
        claim_id=created.id,
    )

    assert claim.id == created.id
    assert claim.claim_text == "Vendor verification completed"


def test_get_missing_claim_raises_error(db_session):
    service = ClaimService()

    try:
        service.get_claim(
            db=db_session,
            claim_id=999999,
        )
    except ValueError as exc:
        assert str(exc) == "Agent claim not found"
    else:
        raise AssertionError("Expected ValueError")