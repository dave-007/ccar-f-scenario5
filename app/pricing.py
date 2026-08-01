from dataclasses import dataclass


@dataclass
class Item:
    name: str
    unit_price: float
    quantity: int


def calculate_subtotal(items: list[Item]) -> float:
    return sum(item.unit_price * item.quantity for item in items)


def bulk_discount_rate(total_quantity: int) -> float:
    if total_quantity > 20:
        return 0.15
    if total_quantity > 10:
        return 0.10
    return 0.0


def apply_flat_discount(total: float, discount_amount: float) -> float:
    return max(0.0, total - discount_amount)


def calculate_total(items: list[Item], tax_rate: float) -> float:
    subtotal = calculate_subtotal(items)
    taxed = subtotal * (1 + tax_rate)
    total_quantity = sum(item.quantity for item in items)
    discount = bulk_discount_rate(total_quantity)
    return round(taxed * (1 - discount), 2)
