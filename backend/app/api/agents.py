from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.agent import Agent


router = APIRouter(
    prefix="/api/agents",
    tags=["agents"],
)


@router.post("")
def create_agent(
    name: str,
    description: str | None = None,
    allowed_tools: list[str] | None = None,
    db: Session = Depends(get_db),
):
    agent = Agent(
        name=name,
        description=description,
        allowed_tools=allowed_tools or [],
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "is_active": agent.is_active,
        "allowed_tools": agent.allowed_tools,
        "created_at": agent.created_at,
    }


@router.patch("/{agent_id}/permissions")
def update_agent_permissions(
    agent_id: int,
    allowed_tools: list[str],
    db: Session = Depends(get_db),
):
    agent = db.get(Agent, agent_id)

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    agent.allowed_tools = allowed_tools

    db.commit()
    db.refresh(agent)

    return {
        "id": agent.id,
        "name": agent.name,
        "allowed_tools": agent.allowed_tools,
    }