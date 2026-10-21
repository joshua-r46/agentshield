from sqlalchemy.orm import Session

from app.schemas.security import SecurityDecision, ToolRequest
from app.services.security.enforcement import (
    SecureToolExecutor,
    ToolExecutionBlocked,
)
from app.services.tools.registry import ToolRegistry
from app.services.policy.engine import PolicyEngine
from app.services.security.interceptor import AgentShieldInterceptor


class AgentShieldService:
    def __init__(
        self,
        interceptor: AgentShieldInterceptor,
        registry: ToolRegistry,
        policy_engine: PolicyEngine,
        executor: SecureToolExecutor,
    ):
        self.interceptor = interceptor
        self.registry = registry
        self.policy_engine = policy_engine
        self.executor = executor

    def evaluate(
        self,
        request: ToolRequest,
        db: Session,
    ) -> SecurityDecision:
        policy_result = self.policy_engine.evaluate(request)

        if not policy_result.allowed:
            return SecurityDecision(
                decision="BLOCK",
                risk_score=100,
                reasons=policy_result.reasons,
            )

        return self.interceptor.evaluate(
            request=request,
            db=db,
        )

    def execute(
        self,
        request: ToolRequest,
        db: Session,
    ):
        return self.executor.execute(
            request=request,
            db=db,
        )