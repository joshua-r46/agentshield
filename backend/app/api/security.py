from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.security import SecurityDecision, ToolRequest
from app.services.policy.engine import PolicyEngine
from app.services.security.enforcement import SecureToolExecutor
from app.services.security.interceptor import AgentShieldInterceptor
from app.services.security.service import AgentShieldService
from app.services.tools.registry import ToolRegistry
from app.services.tools.fake_bank import FakeBankAPI


router = APIRouter(
    prefix="/api/security",
    tags=["security"],
)


interceptor = AgentShieldInterceptor()
policy_engine = PolicyEngine()

registry = ToolRegistry()

fake_bank = FakeBankAPI()

registry.register(
    "transfer_money",
    fake_bank.transfer_money,
)
registry.register(
    "verify_vendor",
    fake_bank.verify_vendor,
)
registry.register(
    "send_email",
    fake_bank.send_email,
)
executor = SecureToolExecutor(
    interceptor=interceptor,
    registry=registry,
    policy_engine=policy_engine,
)

security_service = AgentShieldService(
    interceptor=interceptor,
    registry=registry,
    policy_engine=policy_engine,
    executor=executor,
)


@router.post(
    "/evaluate",
    response_model=SecurityDecision,
)
def evaluate_security(
    request: ToolRequest,
    db: Session = Depends(get_db),
) -> SecurityDecision:
    return security_service.evaluate(
        request=request,
        db=db,
    )