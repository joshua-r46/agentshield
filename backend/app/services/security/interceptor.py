from sqlalchemy.orm import Session

from app.schemas.security import SecurityDecision, ToolRequest
from app.services.consequence.engine import ConsequenceEngine
from app.services.risk.engine import RiskEngine
from app.services.security.anomaly import BehavioralAnomalyEngine


class AgentShieldInterceptor:
    def __init__(
        self,
        risk_engine: RiskEngine | None = None,
        consequence_engine: ConsequenceEngine | None = None,
        anomaly_engine: BehavioralAnomalyEngine | None = None,
    ):
        self.risk_engine = risk_engine or RiskEngine()
        self.consequence_engine = consequence_engine or ConsequenceEngine()
        self.anomaly_engine = anomaly_engine or BehavioralAnomalyEngine()

    def evaluate(
        self,
        request: ToolRequest,
        db: Session | None = None,
    ) -> SecurityDecision:
        risk = self.risk_engine.assess(
            request=request,
            db=db,
    )
        consequence = self.consequence_engine.assess(request)

        combined_score = risk.score

        if consequence.severity >= 70:
            combined_score = min(combined_score + 30, 100)

        reasons = [
            *risk.reasons,
            *consequence.consequences,
        ]

        # Behavioral anomaly detection requires execution history.
        # Keep it optional so callers that do not have a database session
        # can still perform the basic security evaluation.
        if db is not None:
            anomaly = self.anomaly_engine.assess(
                db=db,
                request=request,
            )

            reasons.extend(anomaly.reasons)

            # Only a strong combined behavioral anomaly changes the
            # security score. Lower anomaly scores remain contextual
            # evidence rather than immediately blocking normal actions.
            if anomaly.score >= 80:
                combined_score = min(combined_score + 20, 100)

        if combined_score >= 71:
            decision = "BLOCK"
        elif combined_score >= 31:
            decision = "REQUIRE_APPROVAL"
        else:
            decision = "ALLOW"

        return SecurityDecision(
            decision=decision,
            risk_score=combined_score,
            reasons=reasons,
        )