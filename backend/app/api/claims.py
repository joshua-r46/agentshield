from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.verification.claim_service import ClaimService
from app.services.verification.verifier import ClaimVerificationService

router = APIRouter(
    prefix="/api/claims",
    tags=["claims"],
)

claim_service = ClaimService()
verification_service = ClaimVerificationService()


@router.post("")
def create_claim(
    agent_id: int,
    claim_type: str,
    claim_text: str,
    claimed_tool: str | None = None,
    claimed_arguments: dict | None = None,
    db: Session = Depends(get_db),
):
    try:
        claim = claim_service.create_claim(
            db=db,
            agent_id=agent_id,
            claim_type=claim_type,
            claim_text=claim_text,
            claimed_tool=claimed_tool,
            claimed_arguments=claimed_arguments,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "id": claim.id,
        "agent_id": claim.agent_id,
        "claim_type": claim.claim_type,
        "claim_text": claim.claim_text,
        "claimed_tool": claim.claimed_tool,
        "claimed_arguments": claim.claimed_arguments,
        "verification_status": claim.verification_status,
        "created_at": claim.created_at,
    }


@router.post("/{claim_id}/verify")
def verify_claim(
    claim_id: int,
    db: Session = Depends(get_db),
):
    try:
        claim = verification_service.verify_claim(
            db=db,
            claim_id=claim_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return {
        "id": claim.id,
        "agent_id": claim.agent_id,
        "claim_type": claim.claim_type,
        "claim_text": claim.claim_text,
        "claimed_tool": claim.claimed_tool,
        "claimed_arguments": claim.claimed_arguments,
        "verification_status": claim.verification_status,
    }