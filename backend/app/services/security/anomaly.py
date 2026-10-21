from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.execution_trace import ExecutionTrace
from app.schemas.security import ToolRequest


@dataclass(frozen=True)
class AnomalyAssessment:
    score: int
    reasons: list[str]


class BehavioralAnomalyEngine:
    def assess(
        self,
        db: Session,
        request: ToolRequest,
    ) -> AnomalyAssessment:
        score = 0
        reasons: list[str] = []

        traces = (
            db.query(ExecutionTrace)
            .filter(
                ExecutionTrace.agent_id == request.agent_id,
                ExecutionTrace.execution_status == "SUCCESS",
            )
            .all()
        )

        known_tools = {trace.tool for trace in traces}

        if request.tool not in known_tools:
            score += 40
            reasons.append("Tool is unusual for this agent")

        if request.tool == "transfer_money":
            amount = request.arguments.get("amount", 0)

            previous_amounts = [
                trace.arguments.get("amount")
                for trace in traces
                if trace.tool == "transfer_money"
                and isinstance(trace.arguments.get("amount"), (int, float))
            ]

            if (
                isinstance(amount, (int, float))
                and previous_amounts
                and amount > max(previous_amounts) * 2
            ):
                score += 40
                reasons.append("Transfer amount is unusually high for this agent")

        score = min(score, 100)

        return AnomalyAssessment(
            score=score,
            reasons=reasons,
        )