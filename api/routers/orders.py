import fastapi
from sqlalchemy.exc import IntegrityError

from api.dependencies import get_repository
from repository.crud.orders import OrdersCRUDRepository
from models.schemas.orders import OrderCreateIn, OrderOut
from securities.permissions import get_current_customer_id, authorize_order_access


router = fastapi.APIRouter(prefix="/orders", tags=["orders"])

@router.post(
    path="/create-new",
    name="orders:create-order",
    response_model=OrderOut,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def create_order(
    order_create: OrderCreateIn,
    current_customer_id: str = fastapi.Depends(get_current_customer_id),
    order_repo: OrdersCRUDRepository = fastapi.Depends(get_repository(repo_type=OrdersCRUDRepository)),
):
    authorize_order_access(current_customer_id, order_create.customer_id)
    try:
        order = await order_repo.create_order(order_in=order_create)
    except IntegrityError:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Integrity error",
        )
    return order


@router.get(path="/{order_id}", response_model=OrderOut, name="orders:get-order")
async def get_order(
    order_id: int,
    current_customer_id: str = fastapi.Depends(get_current_customer_id),
    order_repo: OrdersCRUDRepository = fastapi.Depends(get_repository(repo_type=OrdersCRUDRepository)),
):
    order = await order_repo.get_order(order_id)
    if not order:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND, detail="Order not found")
    authorize_order_access(current_customer_id, order.customer_id)
    return order


