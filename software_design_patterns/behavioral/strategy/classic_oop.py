from abc import ABC
from abc import abstractmethod


# ==========================================
# 1. THE STRATEGY INTERFACE
# ==========================================
class ShippingStrategy(ABC):
    @abstractmethod
    def calculate(self, subtotal: float, total_weight: float) -> float:
        """Calculate shipping cost."""
        pass


# ==========================================
# 2. CONCRETE STRATEGIES (Each algorithm in its own class)
# ==========================================
class StandardShipping(ShippingStrategy):
    def calculate(self, subtotal: float, total_weight: float) -> float:
        return 5.0


class ExpressShipping(ShippingStrategy):
    def calculate(self, subtotal: float, total_weight: float) -> float:
        return 15.0


class WeightBasedShipping(ShippingStrategy):
    def calculate(self, subtotal: float, total_weight: float) -> float:
        return total_weight * 2.0


class FreeShipping(ShippingStrategy):
    def calculate(self, subtotal: float, total_weight: float) -> float:
        return 0.0 if subtotal >= 100 else 10.0


# ==========================================
# 3. THE CONTEXT (Uses the strategy)
# ==========================================
class Checkout:
    def __init__(self, items: list, shipping_strategy: ShippingStrategy):
        self.items = items
        self.shipping_strategy = shipping_strategy

    def calculate_total(self) -> float:
        subtotal = sum(item.price * item.quantity for item in self.items)
        total_weight = sum(item.weight * item.quantity for item in self.items)

        # Delegate to the strategy — no if/else!
        shipping = self.shipping_strategy.calculate(subtotal, total_weight)

        return subtotal + shipping


# ==========================================
# 4. USAGE
# ==========================================
class Item:
    def __init__(self, name: str, price: float, weight: float, quantity: int = 1):
        self.name = name
        self.price = price
        self.weight = weight
        self.quantity = quantity


if __name__ == '__main__':
    # Create some items
    items = [
        Item("Laptop", 999.99, 2.5),
        Item("Mouse", 29.99, 0.2),
    ]

    # Use different strategies at runtime
    checkout_standard = Checkout(items, StandardShipping())
    print(f"Standard: ${checkout_standard.calculate_total():.2f}")

    checkout_express = Checkout(items, ExpressShipping())
    print(f"Express: ${checkout_express.calculate_total():.2f}")

    checkout_weight = Checkout(items, WeightBasedShipping())
    print(f"Weight-based: ${checkout_weight.calculate_total():.2f}")

    # Want to add a new strategy? Just create a new class!
    # No need to modify Checkout at all.
