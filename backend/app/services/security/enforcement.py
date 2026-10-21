from typing import Any

from sqlalchemy.orm import Session

from app.schemas.security import SecurityDecision, ToolRequest
from app.services.approval.service import ApprovalService
from app.services.audit.service import AuditService
from app.services.policy.engine import PolicyEngine
from app.services.security.interceptor import AgentShieldInterceptor
from app.services.tools.registry import ToolRegistry
from app.services.verification.trace_service import ExecutionTraceService


class ToolExecutionBlocked(Exception):
    def __init__(
        self,
        decision: SecurityDecision,
        approval_id: int | None = None,
    ):
        self.decision = decision
        self.approval_id = approval_id

        super().__init__(
            f"Tool execution blocked: "
            f"risk={decision.risk_score}, "
            f"decision={decision.decision}"
        )


class SecureToolExecutor:
    def __init__(
        self,
        interceptor,
        registry,
        policy_engine,
        audit_service=None,
        approval_service=None,
        trace_service=None,
    ):
        self.interceptor = interceptor
        self.registry = registry
        self.policy_engine = policy_engine
        self.audit_service = audit_service or AuditService()
        self.approval_service = approval_service or ApprovalService()
        self.trace_service = trace_service or ExecutionTraceService()

    def _evaluate_security(
        self,
        request: ToolRequest,
        db: Session,
    ) -> SecurityDecision:
        """
        Run the interceptor's security evaluation.

        Permission enforcement is handled separately from the
        risk/consequence calculation. The interceptor is therefore
        evaluated without a database session here.
        """
        return self.interceptor.evaluate(
            request=request,
            db=db,
        )

    def _execute_tool(
        self,
        request: ToolRequest,
        db: Session,
        decision: SecurityDecision,
    ) -> tuple[SecurityDecision, Any]:

        tool = self.registry.get(request.tool)

        tool_arguments = dict(request.arguments)

        # Security metadata must never be passed
        # to the actual tool.
        tool_arguments.pop("vendor_verified", None)

        try:
            result = tool(**tool_arguments)

            trace_result = result

            if hasattr(result, "__dict__"):
                trace_result = result.__dict__

            self.trace_service.record_execution(
                db=db,
                agent_id=request.agent_id,
                tool=request.tool,
                arguments=request.arguments,
                execution_status="SUCCESS",
                result=trace_result,
            )

            return decision, result

        except Exception as exc:
            self.trace_service.record_execution(
                db=db,
                agent_id=request.agent_id,
                tool=request.tool,
                arguments=request.arguments,
                execution_status="FAILED",
                result={
                    "error": str(exc),
                },
            )

            raise

    def execute(
        self,
        request: ToolRequest,
        db: Session,
    ) -> tuple[SecurityDecision, Any]:

        # ---------------------------------------------------------
        # 1. POLICY CHECK
        # ---------------------------------------------------------
        policy_result = self.policy_engine.evaluate(request)

        if not policy_result.allowed:
            decision = SecurityDecision(
                decision="BLOCK",
                risk_score=100,
                reasons=policy_result.reasons,
            )

            self.audit_service.log_security_decision(
                db=db,
                request=request,
                decision=decision,
                message="Tool execution blocked by policy",
            )

            raise ToolExecutionBlocked(
                decision=decision,
            )

        # ---------------------------------------------------------
        # 2. SECURITY INTERCEPTOR
        # ---------------------------------------------------------
        decision = self._evaluate_security(
            request=request,
            db=db,
        )

        self.audit_service.log_security_decision(
            db=db,
            request=request,
            decision=decision,
            message="Tool execution security decision",
        )

        # ---------------------------------------------------------
        # 3. REQUIRE HUMAN APPROVAL
        # ---------------------------------------------------------
        if decision.decision == "REQUIRE_APPROVAL":
            approval = self.approval_service.create_approval(
                db=db,
                request=request,
                decision=decision,
            )

            raise ToolExecutionBlocked(
                decision=decision,
                approval_id=approval.id,
            )

        # ---------------------------------------------------------
        # 4. BLOCK
        # ---------------------------------------------------------
        if decision.decision == "BLOCK":
            raise ToolExecutionBlocked(
                decision=decision,
            )

        # ---------------------------------------------------------
        # 5. EXECUTE ALLOWED TOOL
        # ---------------------------------------------------------
        return self._execute_tool(
            request=request,
            db=db,
            decision=decision,
        )

    def execute_approved(
        self,
        approval_id: int,
        db: Session,
    ) -> tuple[SecurityDecision, Any]:

        # ---------------------------------------------------------
        # 1. LOAD APPROVAL
        # ---------------------------------------------------------
        approval = self.approval_service.get_approval(
            db=db,
            approval_id=approval_id,
        )

        # ---------------------------------------------------------
        # 2. APPROVAL MUST ACTUALLY BE APPROVED
        # ---------------------------------------------------------
        if approval.status != "APPROVED":
            decision = SecurityDecision(
                decision="BLOCK",
                risk_score=100,
                reasons=[
                    "Approval is not approved",
                ],
            )

            raise ToolExecutionBlocked(
                decision=decision,
                approval_id=approval.id,
            )

        # ---------------------------------------------------------
        # 3. REBUILD ORIGINAL TOOL REQUEST
        # ---------------------------------------------------------
        request = self.approval_service.build_tool_request(
            approval,
        )

        # ---------------------------------------------------------
        # 4. RE-RUN POLICY CHECK
        # ---------------------------------------------------------
        policy_result = self.policy_engine.evaluate(request)

        if not policy_result.allowed:
            decision = SecurityDecision(
                decision="BLOCK",
                risk_score=100,
                reasons=policy_result.reasons,
            )

            self.audit_service.log_security_decision(
                db=db,
                request=request,
                decision=decision,
                message="Approved action blocked during re-validation",
            )

            raise ToolExecutionBlocked(
                decision=decision,
                approval_id=approval.id,
            )

        # ---------------------------------------------------------
        # 5. RE-RUN SECURITY INTERCEPTOR
        # ---------------------------------------------------------
        decision = self._evaluate_security(
            request=request,
            db=db,
        )

        self.audit_service.log_security_decision(
            db=db,
            request=request,
            decision=decision,
            message="Approved action re-validated",
        )

        # ---------------------------------------------------------
        # 6. BLOCK ONLY IF RE-VALIDATION BLOCKS THE ACTION
        #
        # Existing human approval satisfies REQUIRE_APPROVAL.
        # ---------------------------------------------------------
        if decision.decision == "BLOCK":
            raise ToolExecutionBlocked(
                decision=decision,
                approval_id=approval.id,
            )

        # ---------------------------------------------------------
        # 7. EXECUTE APPROVED TOOL
        # ---------------------------------------------------------
        return self._execute_tool(
            request=request,
            db=db,
            decision=decision,
        )