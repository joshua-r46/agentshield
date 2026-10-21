from sqlalchemy.orm import Session

from app.schemas.security import ToolRequest
from app.services.security.service import AgentShieldService
from app.services.security.enforcement import ToolExecutionBlocked

class AgentRunner:
    def __init__(
        self,
        security_service: AgentShieldService,
    ):
        self.security_service = security_service

    def propose_action(
        self,
        db: Session,
        agent_id: int,
        tool: str,
        arguments: dict,
    ):
        request = ToolRequest(
            agent_id=agent_id,
            tool=tool,
            arguments=arguments,
        )

        return self.security_service.evaluate(
            request=request,
            db=db,
        )

    def execute_action(
        self,
        db: Session,
        agent_id: int,
        tool: str,
        arguments: dict,
    ):
        request = ToolRequest(
            agent_id=agent_id,
            tool=tool,
            arguments=arguments,
        )

        return self.security_service.execute(
            request=request,
            db=db,
        )
    
    def execute_plan(
        self,
        db: Session,
        agent_id: int,
        actions: list[dict],
    ):
        results = []

        for action in actions:
            tool = action["tool"]
            arguments = action.get("arguments", {})

            try:
                result = self.execute_action(
                    db=db,
                    agent_id=agent_id,
                    tool=tool,
                    arguments=arguments,
                )

                results.append(
                    {
                        "tool": tool,
                        "status": "EXECUTED",
                        "result": result,
                    }
                )

            except ToolExecutionBlocked as exc:
                if exc.decision.decision == "REQUIRE_APPROVAL":
                    return {
                        "status": "REQUIRES_APPROVAL",
                        "approval_id": exc.approval_id,
                        "completed_actions": results,
                    }

                raise

        return {
            "status": "COMPLETED",
            "completed_actions": results,
        }
	