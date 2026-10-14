from abc import ABC
from abc import abstractmethod
from typing import List


# ==========================================
# 1. THE OBSERVER INTERFACE
# ==========================================
class OrderObserver(ABC):
    @abstractmethod
    def on_order_placed(self, order: dict):
        """Called when an order is placed."""
        pass


# ==========================================
# 2. CONCRETE OBSERVERS (Each handles its own logic)
# ==========================================
class EmailNotificationObserver(OrderObserver):
    def on_order_placed(self, order: dict):
        print(f"[Email] Sending confirmation to {order['user_email']} for order #{order['id']}")


class InventoryObserver(OrderObserver):
    def on_order_placed(self, order: dict):
        print(f"[Inventory] Decreasing stock for {len(order['items'])} items")


class WarehouseObserver(OrderObserver):
    def on_order_placed(self, order: dict):
        print(f"[Warehouse] Preparing shipment for order #{order['id']}")


class AnalyticsObserver(OrderObserver):
    def on_order_placed(self, order: dict):
        print(f"[Analytics] Tracking order #{order['id']} — total: ${order['total']}")


# ==========================================
# 3. THE SUBJECT (Maintains observers and notifies them)
# ==========================================
class OrderService:
    def __init__(self):
        self._observers: List[OrderObserver] = []

    def attach(self, observer: OrderObserver):
        """Register an observer."""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: OrderObserver):
        """Unregister an observer."""
        self._observers.remove(observer)

    def _notify_observers(self, order: dict):
        """Notify all registered observers."""
        for observer in self._observers:
            observer.on_order_placed(order)

    def place_order(self, user_email: str, items: list, total: float) -> dict:
        """Place an order and notify observers."""
        order = {
            "id": "ORD-12345",
            "user_email": user_email,
            "items": items,
            "total": total,
            "status": "placed"
        }

        # Save to database
        print(f"[OrderService] Saving order {order['id']} to database...")

        # Notify all observers — OrderService doesn't know what they do!
        self._notify_observers(order)

        return order


# ==========================================
# 4. USAGE
# ==========================================
if __name__ == "__main__":
    # Create the subject
    order_service = OrderService()

    # Attach observers (can be done in different modules, at startup)
    order_service.attach(EmailNotificationObserver())
    order_service.attach(InventoryObserver())
    order_service.attach(WarehouseObserver())
    order_service.attach(AnalyticsObserver())

    # Place an order — observers are notified automatically
    order = order_service.place_order(
        user_email="alice@example.com",
        items=[{"product": "Laptop", "qty": 1}],
        total=999.99
    )
