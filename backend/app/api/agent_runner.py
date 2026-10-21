from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.agent.runner import AgentRunner
from app.services.approval.service import ApprovalService
from app.services.policy.engine import PolicyEngine
from app.services.security.enforcement import (
    SecureToolExecutor,
    ToolExecutionBlocked,
)
from app.services.security.interceptor import AgentShieldInterceptor
from app.services.security.service import AgentShieldService
from app.services.tools.fake_bank import FakeBankAPI
from app.services.tools.registry import ToolRegistry


router = APIRouter(
    prefix="/api/agent",
    tags=["agent"],
)


interceptor = AgentShieldInterceptor()
policy_engine = PolicyEngine()

registry = ToolRegistry()

fake_bank = FakeBankAPI()

registry.register(
    "transfer_money",
    fake_bank.transfer_money,
)

registry.register(
    "verify_vendor",
    fake_bank.verify_vendor,
)
registry.register(
    "send_email",
    fake_bank.send_email,
)

approval_service = ApprovalService()

executor = SecureToolExecutor(
    interceptor=interceptor,
    registry=registry,
    policy_engine=policy_engine,
    approval_service=approval_service,
)

security_service = AgentShieldService(
    interceptor=interceptor,
    registry=registry,
    policy_engine=policy_engine,
    executor=executor,
)

agent_runner = AgentRunner(
    security_service=security_service,
)


@router.post("/run")
def run_agent_plan(
    agent_id: int,
    actions: list[dict],
    db: Session = Depends(get_db),
):
    try:
        result = agent_runner.execute_plan(
            db=db,
            agent_id=agent_id,
            actions=actions,
        )

        return result

    except ToolExecutionBlocked as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "decision": exc.decision.decision,
                "risk_score": exc.decision.risk_score,
                "reasons": exc.decision.reasons,
                "approval_id": exc.approval_id,
            },
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )