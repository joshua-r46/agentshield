from app.schemas.security import ToolRequest
from app.services.policy.engine import PolicyEngine


def test_valid_transfer_is_allowed():
    engine = PolicyEngine()

    request = ToolRequest(
        agent_id=1,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    result = engine.evaluate(request)

    assert result.allowed is True
    assert result.reasons == []


def test_negative_transfer_is_rejected():
    engine = PolicyEngine()

    request = ToolRequest(
        agent_id=1,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": -100,
            "vendor_verified": True,
        },
    )

    result = engine.evaluate(request)

    assert result.allowed is False
    assert "Transfer amount must be greater than zero" in result.reasons


def test_blocked_vendor_is_rejected():
    engine = PolicyEngine()

    request = ToolRequest(
        agent_id=1,
        tool="transfer_money",
        arguments={
            "recipient": "blocked_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    result = engine.evaluate(request)

    assert result.allowed is False
    assert "Recipient is blocked" in result.reasons