from dataclasses import dataclass

from app.schemas.security import ToolRequest


@dataclass(frozen=True)
class ConsequenceAssessment:
    severity: int
    consequences: list[str]


class ConsequenceEngine:
    """
    Determines the potential consequences of a tool action.

    The consequence engine does not decide whether an action is
    allowed. It describes the impact if the action succeeds.
    """

    def assess(self, request: ToolRequest) -> ConsequenceAssessment:
        severity = 0
        consequences: list[str] = []

        if request.tool == "transfer_money":
            severity = 40
            consequences.append("Financial loss is possible")
            consequences.append("External financial side effect")

            amount = request.arguments.get("amount", 0)

            if isinstance(amount, (int, float)) and amount > 50_000:
                severity += 30
                consequences.append("High-value financial impact")

        severity = min(severity, 100)

        return ConsequenceAssessment(
            severity=severity,
            consequences=consequences,
        )