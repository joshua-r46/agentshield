from app.schemas.security import ToolRequest
from app.services.consequence.engine import ConsequenceEngine


def test_financial_action_has_consequences():
    engine = ConsequenceEngine()

    request = ToolRequest(
        agent_id=1,
        tool="transfer_money",
        arguments={
            "recipient": "trusted_vendor",
            "amount": 1000,
            "vendor_verified": True,
        },
    )

    result = engine.assess(request)

    assert result.severity == 40
    assert "Financial loss is possible" in result.consequences
    assert "External financial side effect" in result.consequences


def test_high_value_transfer_has_higher_consequence():
    engine = ConsequenceEngine()

    request = ToolRequest(
        agent_id=1,
        tool="transfer_money",
        arguments={
            "recipient": "new_vendor",
            "amount": 80000,
            "vendor_verified": False,
        },
    )

    result = engine.assess(request)

    assert result.severity == 70
    assert "High-value financial impact" in result.consequences


def test_non_financial_action_has_no_consequence():
    engine = ConsequenceEngine()

    request = ToolRequest(
        agent_id=1,
        tool="search_vendor",
        arguments={
            "name": "Acme",
        },
    )

    result = engine.assess(request)

    assert result.severity == 0
    assert result.consequences == []