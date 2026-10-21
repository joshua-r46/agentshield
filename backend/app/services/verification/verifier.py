from sqlalchemy.orm import Session

from app.models.agent_claim import AgentClaim
from app.models.execution_trace import ExecutionTrace


class ClaimVerificationService:
    def verify_claim(
        self,
        db: Session,
        claim_id: int,
    ) -> AgentClaim:
        claim = db.get(AgentClaim, claim_id)

        if claim is None:
            raise ValueError("Agent claim not found")

        if not claim.claimed_tool:
            claim.verification_status = "MISMATCH"
            db.commit()
            db.refresh(claim)
            return claim

        traces = (
            db.query(ExecutionTrace)
            .filter(
                ExecutionTrace.agent_id == claim.agent_id,
                ExecutionTrace.tool == claim.claimed_tool,
                ExecutionTrace.execution_status == "SUCCESS",
            )
            .order_by(ExecutionTrace.created_at.desc())
            .all()
        )

        for trace in traces:
            if self._arguments_match(
                claimed=claim.claimed_arguments,
                actual=trace.arguments,
            ):
                claim.verification_status = "VERIFIED"
                db.commit()
                db.refresh(claim)
                return claim

        claim.verification_status = "MISMATCH"

        db.commit()
        db.refresh(claim)

        return claim

    def _arguments_match(
        self,
        claimed: dict | None,
        actual: dict,
    ) -> bool:
        if claimed is None:
            return True

        for key, value in claimed.items():
            if actual.get(key) != value:
                return False

        return True