from app.pricing import Item, calculate_subtotal, calculate_total


def test_calculate_subtotal_single_item():
    items = [Item(name="widget", unit_price=10.0, quantity=2)]
    assert calculate_subtotal(items) == 20.0


def test_calculate_total_no_discount():
    items = [Item(name="widget", unit_price=10.0, quantity=1)]
    assert calculate_total(items, tax_rate=0.10) == 11.0
