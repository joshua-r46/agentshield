from datetime import datetime

from sqlalchemy.orm import Session

from app.models.approval import Approval
from app.schemas.security import SecurityDecision, ToolRequest


class ApprovalService:
    def create_approval(
        self,
        db: Session,
        request: ToolRequest,
        decision: SecurityDecision,
    ) -> Approval:
        approval = Approval(
            agent_id=request.agent_id,
            tool=request.tool,
            arguments=request.arguments,
            risk_score=decision.risk_score,
            status="PENDING",
            reason="Human approval required for this action",
        )

        db.add(approval)
        db.commit()
        db.refresh(approval)

        return approval

    def get_approval(
        self,
        db: Session,
        approval_id: int,
    ) -> Approval:
        approval = db.get(Approval, approval_id)

        if approval is None:
            raise ValueError("Approval request not found")

        return approval

    def build_tool_request(
        self,
        approval: Approval,
    ) -> ToolRequest:
        return ToolRequest(
            agent_id=approval.agent_id,
            tool=approval.tool,
            arguments=approval.arguments,
        )

    def approve(
        self,
        db: Session,
        approval_id: int,
        reviewed_by: str,
    ) -> Approval:
        approval = db.get(Approval, approval_id)

        if approval is None:
            raise ValueError("Approval request not found")

        if approval.status != "PENDING":
            raise ValueError(
                f"Approval request is already {approval.status}"
            )

        approval.status = "APPROVED"
        approval.reviewed_by = reviewed_by
        approval.reviewed_at = datetime.utcnow()

        db.commit()
        db.refresh(approval)

        return approval

    def reject(
        self,
        db: Session,
        approval_id: int,
        reviewed_by: str,
    ) -> Approval:
        approval = db.get(Approval, approval_id)

        if approval is None:
            raise ValueError("Approval request not found")

        if approval.status != "PENDING":
            raise ValueError(
                f"Approval request is already {approval.status}"
            )

        approval.status = "REJECTED"
        approval.reviewed_by = reviewed_by
        approval.reviewed_at = datetime.utcnow()

        db.commit()
        db.refresh(approval)

        return approval