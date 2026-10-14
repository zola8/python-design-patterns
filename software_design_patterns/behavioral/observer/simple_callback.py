from typing import Callable
from typing import List


class OrderService:
    def __init__(self):
        self._callbacks: List[Callable[[dict], None]] = []

    def on_order_placed(self, callback: Callable[[dict], None]):
        """Register a callback function."""
        self._callbacks.append(callback)

    def _notify(self, order: dict):
        for callback in self._callbacks:
            callback(order)

    def place_order(self, user_email: str, items: list, total: float) -> dict:
        order = {"id": "ORD-123", "user_email": user_email, "items": items, "total": total}
        print(f"[OrderService] Order placed: {order['id']}")
        self._notify(order)
        return order


if __name__ == '__main__':
    order_service = OrderService()

    # Register callbacks (can be lambdas or functions)
    order_service.on_order_placed(lambda order: print(f"[Email] Send to {order['user_email']}"))
    order_service.on_order_placed(lambda order: print(f"[Inventory] Update stock"))
    order_service.on_order_placed(lambda order: print(f"[Analytics] Track {order['id']}"))

    order_service.place_order("bob@example.com", [{"product": "Mouse"}], 29.99)
