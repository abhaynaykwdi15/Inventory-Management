from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.routers.auth import require_user
from app.database import get_connection
from app.repositories import inventory
from app.schemas.inventory import AuditPage, AuditRead
from app.services.database_errors import run_read


router = APIRouter(
    prefix="/audit-logs",
    tags=["audit"],
    dependencies=[Depends(require_user)],
)


@router.get("", response_model=AuditPage)
def get_audit_logs(
    connection: Annotated[object, Depends(get_connection)],
    table_name: Literal["ITEMS", "STOCK", "STOCK_TRANSACTIONS"] | None = None,
    action_type: Literal["INSERT", "UPDATE", "DELETE"] | None = None,
    search: str | None = Query(default=None, max_length=150),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AuditPage:
    result = run_read(
        connection,
        lambda: inventory.list_audit_logs(
            connection,
            table_name=table_name,
            action_type=action_type,
            search=search,
            limit=limit,
            offset=offset,
        ),
    )
    return AuditPage(
        items=[AuditRead.model_validate(row) for row in result["items"]],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )
