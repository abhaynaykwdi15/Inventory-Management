from collections.abc import Callable
import logging
from typing import Any, TypeVar

from fastapi import HTTPException
from mysql.connector import Error as MySQLDatabaseError


T = TypeVar("T")
logger = logging.getLogger(__name__)


class ResourceNotFound(Exception):
    """A requested database resource does not exist."""


class InventoryConflict(Exception):
    """A requested operation conflicts with existing inventory history."""


_APPLICATION_ERRORS: dict[int, tuple[int, str]] = {
    1062: (409, "An item with this SKU already exists."),
}
_PROCEDURE_ERRORS: dict[str, tuple[int, str]] = {
    "Item ID is required.": (422, "Item ID is required."),
    "Quantity must be a positive whole number.": (422, "Quantity must be a positive whole number."),
    "Item does not exist.": (404, "Item does not exist."),
    "Stock record does not exist for this item.": (
        409,
        "Stock record does not exist for this item.",
    ),
    "Insufficient stock for this issue.": (409, "Insufficient stock for this issue."),
}


def _http_error_for_database_error(error: MySQLDatabaseError) -> HTTPException:
    code = error.errno
    logger.error("MySQL operation failed with database error code %s.", code)
    if code == 1644 and error.msg in _PROCEDURE_ERRORS:
        status_code, message = _PROCEDURE_ERRORS[error.msg]
        return HTTPException(status_code=status_code, detail=message)
    if code in _APPLICATION_ERRORS:
        status_code, message = _APPLICATION_ERRORS[code]
        return HTTPException(status_code=status_code, detail=message)
    return HTTPException(status_code=500, detail="The database operation failed.")


def run_read(connection: Any, operation: Callable[[], T]) -> T:
    try:
        return operation()
    except ResourceNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InventoryConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except MySQLDatabaseError as error:
        connection.rollback()
        raise _http_error_for_database_error(error) from error


def run_write(connection: Any, operation: Callable[[], T]) -> T:
    try:
        result = operation()
        connection.commit()
        return result
    except ResourceNotFound as error:
        connection.rollback()
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InventoryConflict as error:
        connection.rollback()
        raise HTTPException(status_code=409, detail=str(error)) from error
    except MySQLDatabaseError as error:
        connection.rollback()
        raise _http_error_for_database_error(error) from error
