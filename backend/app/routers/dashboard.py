from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.routers.auth import require_user
from app.database import get_connection
from app.repositories import inventory
from app.schemas.inventory import DashboardSummary
from app.services.database_errors import run_read


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(require_user)],
)


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    connection: Annotated[object, Depends(get_connection)],
    period_days: int = Query(default=30, ge=1, le=365),
) -> DashboardSummary:
    result = run_read(
        connection,
        lambda: inventory.dashboard_summary(connection, period_days),
    )
    return DashboardSummary.model_validate(result)
