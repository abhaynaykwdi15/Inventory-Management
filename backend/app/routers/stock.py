from typing import Annotated

from fastapi import APIRouter, Depends

from app.routers.auth import require_user
from app.database import get_connection
from app.repositories import inventory
from app.schemas.inventory import (
    LowStockRead,
    StockMovementRequest,
    StockMovementResult,
    StockRead,
)
from app.services.database_errors import run_read, run_write


router = APIRouter(
    prefix="/stock",
    tags=["stock"],
    dependencies=[Depends(require_user)],
)


@router.get("", response_model=list[StockRead])
def get_stock(
    connection: Annotated[object, Depends(get_connection)],
) -> list[StockRead]:
    rows = run_read(connection, lambda: inventory.list_stock(connection))
    return [StockRead.model_validate(row) for row in rows]


@router.get("/low", response_model=list[LowStockRead])
def get_low_stock(
    connection: Annotated[object, Depends(get_connection)],
) -> list[LowStockRead]:
    rows = run_read(connection, lambda: inventory.list_low_stock(connection))
    return [LowStockRead.model_validate(row) for row in rows]


@router.post("/in", response_model=StockMovementResult)
def receive_stock(
    movement: StockMovementRequest,
    connection: Annotated[object, Depends(get_connection)],
    user: Annotated[dict, Depends(require_user)],
) -> StockMovementResult:
    result = run_write(
        connection,
        lambda: inventory.add_stock(
            connection,
            item_id=movement.item_id,
            quantity=movement.quantity,
            remarks=movement.remarks,
            created_by=user["email"],
        ),
    )
    return StockMovementResult.model_validate(result)


@router.post("/out", response_model=StockMovementResult)
def issue_stock(
    movement: StockMovementRequest,
    connection: Annotated[object, Depends(get_connection)],
    user: Annotated[dict, Depends(require_user)],
) -> StockMovementResult:
    result = run_write(
        connection,
        lambda: inventory.issue_stock(
            connection,
            item_id=movement.item_id,
            quantity=movement.quantity,
            remarks=movement.remarks,
            created_by=user["email"],
        ),
    )
    return StockMovementResult.model_validate(result)
