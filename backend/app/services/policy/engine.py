from dataclasses import dataclass

from app.schemas.security import ToolRequest


@dataclass(frozen=True)
class PolicyResult:
    allowed: bool
    reasons: list[str]


class PolicyEngine:
    """
    Deterministic policy checks for AgentShield.

    Policies answer:
    "Is this action permitted according to the configured security rules?"
    """

    def evaluate(self, request: ToolRequest) -> PolicyResult:
        reasons: list[str] = []

        if request.tool == "transfer_money":
            amount = request.arguments.get("amount", 0)

            if not isinstance(amount, (int, float)):
                reasons.append("Invalid transfer amount")

            elif amount <= 0:
                reasons.append("Transfer amount must be greater than zero")

            if request.arguments.get("recipient") == "blocked_vendor":
                reasons.append("Recipient is blocked")

        if reasons:
            return PolicyResult(
                allowed=False,
                reasons=reasons,
            )

        return PolicyResult(
            allowed=True,
            reasons=[],
        )