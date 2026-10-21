from sqlalchemy.orm import Session

from app.models.agent_claim import AgentClaim


class ClaimService:
    def create_claim(
        self,
        db: Session,
        agent_id: int,
        claim_type: str,
        claim_text: str,
        claimed_tool: str | None = None,
        claimed_arguments: dict | None = None,
    ) -> AgentClaim:
        claim = AgentClaim(
            agent_id=agent_id,
            claim_type=claim_type,
            claim_text=claim_text,
            claimed_tool=claimed_tool,
            claimed_arguments=claimed_arguments,
            verification_status="PENDING",
        )

        db.add(claim)
        db.commit()
        db.refresh(claim)

        return claim

    def get_claim(
        self,
        db: Session,
        claim_id: int,
    ) -> AgentClaim:
        claim = db.get(AgentClaim, claim_id)

        if claim is None:
            raise ValueError("Agent claim not found")

        return claim