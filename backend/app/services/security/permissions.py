from sqlalchemy.orm import Session

from app.models.agent import Agent


class AgentPermissionService:
    def get_allowed_tools(
        self,
        db: Session,
        agent_id: int,
    ) -> list[str]:
        agent = db.get(Agent, agent_id)

        if agent is None:
            raise ValueError("Agent not found")

        if not agent.is_active:
            raise ValueError("Agent is inactive")

        return list(agent.allowed_tools)