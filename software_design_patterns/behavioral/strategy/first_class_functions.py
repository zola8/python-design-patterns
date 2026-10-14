from typing import Callable

from behavioral.strategy.classic_oop import Item


# Strategies as simple functions
def standard_shipping(subtotal: float, total_weight: float) -> float:
    return 5.0


def express_shipping(subtotal: float, total_weight: float) -> float:
    return 15.0


def weight_based_shipping(subtotal: float, total_weight: float) -> float:
    return total_weight * 2.0


def free_shipping(subtotal: float, total_weight: float) -> float:
    return 0.0 if subtotal >= 100 else 10.0


# Context accepts a function instead of a strategy object
class Checkout:
    def __init__(self, items: list, shipping_calculator: Callable[[float, float], float]):
        self.items = items
        self.shipping_calculator = shipping_calculator

    def calculate_total(self) -> float:
        subtotal = sum(item.price * item.quantity for item in self.items)
        total_weight = sum(item.weight * item.quantity for item in self.items)
        shipping = self.shipping_calculator(subtotal, total_weight)
        return subtotal + shipping


if __name__ == '__main__':
    items = [
        Item("Laptop", 999.99, 2.5),
        Item("Mouse", 29.99, 0.2),
    ]

    # Usage — even cleaner!
    checkout = Checkout(items, weight_based_shipping)
    print(f"Total: ${checkout.calculate_total():.2f}")
