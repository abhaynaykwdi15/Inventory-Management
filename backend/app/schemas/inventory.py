from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ItemWrite(BaseModel):
    sku: str = Field(min_length=1, max_length=40)
    item_name: str = Field(min_length=1, max_length=150)
    category: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=1000)
    unit_price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    reorder_level: int = Field(ge=0, le=9_999_999_999, strict=True)

    @field_validator("sku", "item_name", "category")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("description")
    @classmethod
    def strip_optional_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ItemRead(BaseModel):
    item_id: int
    sku: str
    item_name: str
    category: str
    description: str | None
    unit_price: Decimal
    reorder_level: int
    quantity_on_hand: int
    created_at: datetime
    updated_at: datetime


class ItemPage(BaseModel):
    items: list[ItemRead]
    total: int
    limit: int
    offset: int


class StockMovementRequest(BaseModel):
    item_id: int = Field(gt=0, strict=True)
    quantity: int = Field(gt=0, le=9_999_999_999, strict=True)
    remarks: str | None = Field(default=None, max_length=500)

    @field_validator("remarks")
    @classmethod
    def strip_remarks(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

class StockMovementResult(BaseModel):
    message: str
    item_id: int
    quantity_on_hand: int


class StockRead(BaseModel):
    stock_id: int
    item_id: int
    sku: str
    item_name: str
    category: str
    quantity_on_hand: int
    reorder_level: int
    updated_at: datetime


class LowStockRead(BaseModel):
    item_id: int
    sku: str
    item_name: str
    category: str
    quantity_on_hand: int
    reorder_level: int
    shortage_quantity: int


class TransactionRead(BaseModel):
    transaction_id: int
    item_id: int
    sku: str
    item_name: str
    transaction_type: Literal["IN", "OUT"]
    quantity: int
    transaction_date: datetime
    remarks: str | None
    reference_number: str | None
    created_by: str


class TransactionPage(BaseModel):
    items: list[TransactionRead]
    total: int
    limit: int
    offset: int


class SlowMovingRead(BaseModel):
    item_id: int
    sku: str
    item_name: str
    category: str
    quantity_on_hand: int
    last_issue_date: datetime | None
    days_since_last_issue: int | None
    report_status: Literal["NEVER_ISSUED", "INACTIVE"]


class CurrentStockRead(BaseModel):
    item_id: int
    sku: str
    item_name: str
    category: str
    quantity_on_hand: int
    reorder_level: int
    updated_at: datetime | None


class CurrentStockItemOption(BaseModel):
    item_id: int
    item_name: str
    sku: str
    category: str


class CurrentStockSummary(BaseModel):
    total_items: int
    total_units: int
    low_stock_items: int
    out_of_stock_items: int


class CurrentStockPage(BaseModel):
    items: list[CurrentStockRead]
    total: int
    limit: int
    offset: int
    summary: CurrentStockSummary


class AuditRead(BaseModel):
    audit_id: int
    table_name: str
    record_id: int
    action_type: Literal["INSERT", "UPDATE", "DELETE"]
    old_value: str | None
    new_value: str | None
    changed_by: str
    action_timestamp: datetime


class AuditPage(BaseModel):
    items: list[AuditRead]
    total: int
    limit: int
    offset: int


class CategoryStockRead(BaseModel):
    category: str
    quantity_on_hand: int


class MovementDayRead(BaseModel):
    transaction_day: datetime
    stock_in: int
    stock_out: int


class DashboardSummary(BaseModel):
    period_days: int
    total_unique_items: int
    total_units_in_stock: int
    low_stock_items: int
    out_of_stock_items: int
    stock_received_in_period: int
    stock_issued_in_period: int
    stock_by_category: list[CategoryStockRead]
    movement_by_day: list[MovementDayRead]
    low_stock_comparison: list[LowStockRead]
    recent_transactions: list[TransactionRead]


class HealthRead(BaseModel):
    status: Literal["ok"]
    database: Literal["connected"]


ItemSort = Literal["item_name", "sku", "category", "unit_price", "quantity_on_hand"]
CurrentStockSort = Literal[
    "item_name",
    "sku",
    "category",
    "quantity_on_hand",
    "reorder_level",
    "updated_at",
]
SortDirection = Literal["asc", "desc"]
TransactionType = Literal["IN", "OUT"]
