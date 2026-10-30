from typing import Annotated

from fastapi import APIRouter, Depends

from app.database import get_connection
from app.repositories import inventory
from app.schemas.inventory import HealthRead
from app.services.database_errors import run_read


router = APIRouter()


@router.get("/status")
def status() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health", response_model=HealthRead)
def health(connection: Annotated[object, Depends(get_connection)]) -> HealthRead:
    run_read(connection, lambda: inventory.health_check(connection))
    return HealthRead(status="ok", database="connected")
