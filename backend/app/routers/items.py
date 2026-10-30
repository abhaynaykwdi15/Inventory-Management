from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.routers.auth import require_user
from app.database import get_connection
from app.repositories import inventory
from app.schemas.inventory import ItemPage, ItemRead, ItemSort, ItemWrite, SortDirection
from app.services.database_errors import run_read, run_write


router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(require_user)],
)


@router.get("", response_model=ItemPage)
def get_items(
    connection: Annotated[object, Depends(get_connection)],
    search: str | None = Query(default=None, max_length=150),
    category: str | None = Query(default=None, max_length=80),
    sort_by: ItemSort = "item_name",
    direction: SortDirection = "asc",
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ItemPage:
    result = run_read(
        connection,
        lambda: inventory.list_items(
            connection,
            search=search,
            category=category,
            sort_by=sort_by,
            direction=direction,
            limit=limit,
            offset=offset,
        ),
    )
    return ItemPage.model_validate(result)


@router.get("/categories", response_model=list[str])
def get_item_categories(
    connection: Annotated[object, Depends(get_connection)],
) -> list[str]:
    return run_read(connection, lambda: inventory.list_item_categories(connection))


@router.get("/{item_id}", response_model=ItemRead)
def get_item(
    item_id: int,
    connection: Annotated[object, Depends(get_connection)],
) -> ItemRead:
    result = run_read(connection, lambda: inventory.get_item(connection, item_id))
    return ItemRead.model_validate(result)


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(
    item: ItemWrite,
    connection: Annotated[object, Depends(get_connection)],
) -> ItemRead:
    result = run_write(connection, lambda: inventory.create_item(connection, item.model_dump()))
    return ItemRead.model_validate(result)


@router.put("/{item_id}", response_model=ItemRead)
def update_item(
    item_id: int,
    item: ItemWrite,
    connection: Annotated[object, Depends(get_connection)],
) -> ItemRead:
    result = run_write(
        connection,
        lambda: inventory.update_item(connection, item_id, item.model_dump()),
    )
    return ItemRead.model_validate(result)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    connection: Annotated[object, Depends(get_connection)],
) -> Response:
    run_write(connection, lambda: inventory.delete_item(connection, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
