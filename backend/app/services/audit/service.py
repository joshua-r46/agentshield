from sqlalchemy.orm import Session

from app.models.security_event import SecurityEvent
from app.schemas.security import SecurityDecision, ToolRequest


class AuditService:
    def log_security_decision(
        self,
        db: Session,
        request: ToolRequest,
        decision: SecurityDecision,
        message: str | None = None,
    ) -> SecurityEvent:
        event = SecurityEvent(
            agent_id=request.agent_id,
            tool=request.tool,
            arguments=request.arguments,
            risk_score=decision.risk_score,
            decision=decision.decision,
            reasons=decision.reasons,
            event_type="SECURITY_DECISION",
            message=message,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return event