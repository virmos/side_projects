import fastapi

from api.dependencies import get_loader, get_repository, get_repository_with_provider
from models.db.price_trie import TriePriceDB
from models.schemas.pricing import CheapestOut, PhoneNumberIn
from repository.crud.pricing import PricingRepository
from services.price_loader import TextPriceListLoader
from services.types import IPriceListLoader


router = fastapi.APIRouter(prefix="/pricing", tags=["pricing"])


@router.post(
    "/cheapest", response_model=CheapestOut, name="pricing:find-cheapest"
)
async def find_cheapest(
    payload: PhoneNumberIn,
    repo: PricingRepository = fastapi.Depends(
        get_repository_with_provider(repo_type=PricingRepository, provider_type=TriePriceDB)
    ),
):
    result = await repo.find_cheapest(payload.phone_number)
    if not result:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND, detail="No operator match"
        )
    operator, price, prefix = result
    return CheapestOut(operator=operator, price=price, prefix=prefix)
