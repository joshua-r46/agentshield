from fastapi.testclient import TestClient

from app.main import app
from app.models.agent import Agent
from app.database.session import get_db


client = TestClient(app)


def test_run_agent_safe_plan(db_session):
    agent = Agent(
        name="API Runner Agent",
        description="Agent runner API test",
        allowed_tools=["transfer_money"],
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/agent/run",
            params={
                "agent_id": agent.id,
            },
            json=[
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

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "COMPLETED"
        assert len(data["completed_actions"]) == 1

    finally:
        app.dependency_overrides.clear()


def test_run_agent_high_risk_plan_is_blocked(db_session):
    agent = Agent(
        name="API Security Agent",
        description="High-risk API test",
        allowed_tools=["transfer_money"],
    )

    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/agent/run",
            params={
                "agent_id": agent.id,
            },
            json=[
                {
                    "tool": "transfer_money",
                    "arguments": {
                        "recipient": "new_vendor",
                        "amount": 80000,
                        "vendor_verified": False,
                    },
                }
            ],
        )

        assert response.status_code == 403

        data = response.json()

        assert data["detail"]["decision"] == "BLOCK"
        assert data["detail"]["risk_score"] == 100

    finally:
        app.dependency_overrides.clear()