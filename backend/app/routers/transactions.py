from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.routers.auth import require_user
from app.database import get_connection
from app.repositories import inventory
from app.schemas.inventory import TransactionPage, TransactionRead, TransactionType
from app.services.database_errors import run_read


router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
    dependencies=[Depends(require_user)],
)


@router.get("", response_model=TransactionPage)
def get_transactions(
    connection: Annotated[object, Depends(get_connection)],
    transaction_type: TransactionType | None = None,
    item_id: int | None = Query(default=None, ge=1),
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> TransactionPage:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be on or before date_to.")
    result = run_read(
        connection,
        lambda: inventory.list_transactions(
            connection,
            transaction_type=transaction_type,
            item_id=item_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        ),
    )
    return TransactionPage(
        items=[TransactionRead.model_validate(row) for row in result["items"]],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )
