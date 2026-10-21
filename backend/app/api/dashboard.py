from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.security_event import SecurityEvent


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_events = db.scalar(
        select(func.count(SecurityEvent.id))
    ) or 0

    blocked_events = db.scalar(
        select(func.count(SecurityEvent.id)).where(
            SecurityEvent.decision == "BLOCK"
        )
    ) or 0

    approval_events = db.scalar(
        select(func.count(SecurityEvent.id)).where(
            SecurityEvent.decision == "REQUIRE_APPROVAL"
        )
    ) or 0

    allowed_events = db.scalar(
        select(func.count(SecurityEvent.id)).where(
            SecurityEvent.decision == "ALLOW"
        )
    ) or 0

    average_risk = db.scalar(
        select(func.avg(SecurityEvent.risk_score))
    )

    recent_events = db.scalars(
        select(SecurityEvent)
        .order_by(SecurityEvent.created_at.desc())
        .limit(10)
    ).all()

    return {
        "summary": {
            "total_events": total_events,
            "blocked_events": blocked_events,
            "approval_events": approval_events,
            "allowed_events": allowed_events,
            "average_risk": round(float(average_risk), 2)
            if average_risk is not None
            else 0,
        },
        "recent_events": [
            {
                "id": event.id,
                "agent_id": event.agent_id,
                "tool": event.tool,
                "risk_score": event.risk_score,
                "decision": event.decision,
                "reasons": event.reasons,
                "event_type": event.event_type,
                "message": event.message,
                "created_at": event.created_at.isoformat(),
            }
            for event in recent_events
        ],
    }