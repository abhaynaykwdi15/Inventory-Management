from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.routers.auth import require_user
from app.database import get_connection
from app.repositories import inventory
from app.schemas.inventory import (
    CurrentStockItemOption,
    CurrentStockPage,
    CurrentStockSort,
    SlowMovingRead,
    SortDirection,
)
from app.services.database_errors import run_read


router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    dependencies=[Depends(require_user)],
)


@router.get("/current-stock/items", response_model=list[CurrentStockItemOption])
def get_current_stock_item_options(
    connection: Annotated[object, Depends(get_connection)],
    category: str | None = Query(default=None, max_length=80),
) -> list[CurrentStockItemOption]:
    rows = run_read(
        connection,
        lambda: inventory.list_current_stock_item_options(connection, category),
    )
    return [CurrentStockItemOption.model_validate(row) for row in rows]


@router.get("/current-stock", response_model=CurrentStockPage)
def get_current_stock(
    connection: Annotated[object, Depends(get_connection)],
    search: str | None = Query(default=None, max_length=150),
    category: str | None = Query(default=None, max_length=80),
    item_id: int | None = Query(default=None, ge=1),
    sort_by: CurrentStockSort = "item_name",
    direction: SortDirection = "asc",
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> CurrentStockPage:
    result = run_read(
        connection,
        lambda: inventory.list_current_stock_report(
            connection,
            search=search,
            category=category,
            item_id=item_id,
            sort_by=sort_by,
            direction=direction,
            limit=limit,
            offset=offset,
        ),
    )
    return CurrentStockPage.model_validate(result)


@router.get("/slow-moving", response_model=list[SlowMovingRead])
def get_slow_moving(
    connection: Annotated[object, Depends(get_connection)],
    days: int = Query(default=30, ge=1, le=36_500),
) -> list[SlowMovingRead]:
    rows = run_read(
        connection,
        lambda: inventory.list_slow_moving(connection, days),
    )
    return [SlowMovingRead.model_validate(row) for row in rows]
