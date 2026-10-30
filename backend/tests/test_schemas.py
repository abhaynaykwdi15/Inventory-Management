import pytest
from pydantic import ValidationError

from app.schemas.inventory import ItemWrite, StockMovementRequest


def test_item_schema_trims_text_and_accepts_nonnegative_values():
    item = ItemWrite(
        sku=" DEMO-NEW-001 ",
        item_name=" New item ",
        category=" Demo ",
        unit_price="12.50",
        reorder_level=0,
    )

    assert item.sku == "DEMO-NEW-001"
    assert item.item_name == "New item"
    assert item.category == "Demo"


@pytest.mark.parametrize("quantity", [0, -1, 1.5])
def test_stock_quantity_must_be_a_positive_whole_number(quantity):
    with pytest.raises(ValidationError):
        StockMovementRequest(item_id=1, quantity=quantity)


def test_item_price_cannot_be_negative():
    with pytest.raises(ValidationError):
        ItemWrite(
            sku="DEMO-NEW-001",
            item_name="New item",
            category="Demo",
            unit_price="-0.01",
            reorder_level=0,
        )
