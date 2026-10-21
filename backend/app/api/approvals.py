from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.security import ToolRequest
from app.services.approval.service import ApprovalService
from app.services.security.interceptor import AgentShieldInterceptor
from app.services.security.enforcement import (
    SecureToolExecutor,
    ToolExecutionBlocked,
)
from app.services.tools.registry import ToolRegistry
from app.services.policy.engine import PolicyEngine
from app.services.tools.fake_bank import FakeBankAPI

router = APIRouter(
    prefix="/api/approvals",
    tags=["approvals"],
)


approval_service = ApprovalService()
interceptor = AgentShieldInterceptor()
policy_engine = PolicyEngine()
registry = ToolRegistry()

fake_bank = FakeBankAPI()

registry.register(
    "transfer_money",
    fake_bank.transfer_money,
)


approval_executor = SecureToolExecutor(
    interceptor=interceptor,
    registry=registry,
    policy_engine=policy_engine,
    approval_service=approval_service,
)


@router.post("")
def create_approval(
    request: ToolRequest,
    db: Session = Depends(get_db),
):
    decision = interceptor.evaluate(request)

    if decision.decision != "REQUIRE_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail={
                "message": "This action does not require human approval",
                "decision": decision.decision,
                "risk_score": decision.risk_score,
                "reasons": decision.reasons,
            },
        )

    approval = approval_service.create_approval(
        db=db,
        request=request,
        decision=decision,
    )

    return {
        "id": approval.id,
        "agent_id": approval.agent_id,
        "tool": approval.tool,
        "arguments": approval.arguments,
        "risk_score": approval.risk_score,
        "status": approval.status,
        "reason": approval.reason,
        "created_at": approval.created_at,
    }


@router.get("/{approval_id}")
def get_approval(
    approval_id: int,
    db: Session = Depends(get_db),
):
    try:
        approval = approval_service.get_approval(
            db=db,
            approval_id=approval_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return {
        "id": approval.id,
        "agent_id": approval.agent_id,
        "tool": approval.tool,
        "arguments": approval.arguments,
        "risk_score": approval.risk_score,
        "status": approval.status,
        "reason": approval.reason,
        "reviewed_by": approval.reviewed_by,
        "reviewed_at": approval.reviewed_at,
        "created_at": approval.created_at,
    }


@router.post("/{approval_id}/approve")
def approve_approval(
    approval_id: int,
    reviewed_by: str,
    db: Session = Depends(get_db),
):
    try:
        approval = approval_service.approve(
            db=db,
            approval_id=approval_id,
            reviewed_by=reviewed_by,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return {
        "id": approval.id,
        "agent_id": approval.agent_id,
        "tool": approval.tool,
        "arguments": approval.arguments,
        "risk_score": approval.risk_score,
        "status": approval.status,
        "reason": approval.reason,
        "reviewed_by": approval.reviewed_by,
        "reviewed_at": approval.reviewed_at,
        "created_at": approval.created_at,
    }


@router.post("/{approval_id}/execute")
def execute_approved_action(
    approval_id: int,
    db: Session = Depends(get_db),
):
    try:
        decision, result = approval_executor.execute_approved(
            approval_id=approval_id,
            db=db,
        )

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

    return {
        "approval_id": approval_id,
        "decision": decision.decision,
        "risk_score": decision.risk_score,
        "reasons": decision.reasons,
        "result": result,
    }