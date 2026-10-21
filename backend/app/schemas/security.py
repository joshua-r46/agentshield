from typing import Any, Literal

from pydantic import BaseModel, Field


Decision = Literal["ALLOW", "REQUIRE_APPROVAL", "BLOCK"]


class ToolRequest(BaseModel):
    agent_id: int
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class SecurityDecision(BaseModel):
    decision: Decision
    risk_score: int = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)