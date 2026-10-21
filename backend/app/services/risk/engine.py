from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.schemas.security import ToolRequest
from app.services.security.permissions import AgentPermissionService


@dataclass(frozen=True)
class RiskAssessment:
    score: int
    reasons: list[str]


class RiskEngine:
    def __init__(
        self,
        permission_service: AgentPermissionService | None = None,
    ):
        self.permission_service = (
            permission_service or AgentPermissionService()
        )

    def assess(
        self,
        request: ToolRequest,
        db: Session | None = None,
    ) -> RiskAssessment:
        score = 0
        reasons: list[str] = []

        if request.tool == "transfer_money":
            amount = request.arguments.get("amount", 0)

            if isinstance(amount, (int, float)) and amount > 50_000:
                score += 60
                reasons.append("High-value financial transaction")

            if request.arguments.get("recipient") == "new_vendor":
                score += 30
                reasons.append("Recipient is new")

            if request.arguments.get("vendor_verified") is not True:
                score += 20
                reasons.append("Vendor has not been verified")

        # Permissions must come from the trusted Agent record.
        if db is not None:
            allowed_tools = self.permission_service.get_allowed_tools(
                db=db,
                agent_id=request.agent_id,
            )

            if request.tool not in allowed_tools:
                score += 60
                reasons.append("Tool is not permitted for this agent")

        score = min(score, 100)

        return RiskAssessment(
            score=score,
            reasons=reasons,
        )