from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.agent import Agent
from app.models.execution_trace import ExecutionTrace
from app.database.session import SessionLocal


client = TestClient(app)


def test_security_api_blocks_high_risk_transfer():
    response = client.post(
        "/api/security/evaluate",
        json={
            "agent_id": 1,
            "tool": "transfer_money",
            "arguments": {
                "recipient": "new_vendor",
                "amount": 80000,
                "vendor_verified": False,
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["decision"] == "BLOCK"
    assert data["risk_score"] == 100
    assert len(data["reasons"]) > 0


def test_security_api_allows_safe_transfer():
    db: Session = SessionLocal()

    try:
        agent = db.get(Agent, 1)

        assert agent is not None

        agent.allowed_tools = ["transfer_money"]

        baseline_trace = ExecutionTrace(
            agent_id=1,
            tool="transfer_money",
            arguments={
                "recipient": "existing_vendor",
                "amount": 1000,
                "vendor_verified": True,
            },
            execution_status="SUCCESS",
            result={
                "success": True,
                "transaction_id": "TX-TEST-001",
            },
        )

        db.add(baseline_trace)
        db.commit()

    finally:
        db.close()

    response = client.post(
        "/api/security/evaluate",
        json={
            "agent_id": 1,
            "tool": "transfer_money",
            "arguments": {
                "recipient": "existing_vendor",
                "amount": 1000,
                "vendor_verified": True,
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["decision"] == "ALLOW"
    assert data["risk_score"] == 0