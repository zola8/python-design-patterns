# Enum with Methods (Simple Cases)

from enum import Enum


class OrderStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELLED, OrderStatus.REFUNDED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: {OrderStatus.REFUNDED},
    OrderStatus.CANCELLED: set(),  # Terminal
    OrderStatus.REFUNDED: set(),  # Terminal
}


class Order:
    def __init__(self):
        self.status = OrderStatus.PENDING

    def transition_to(self, new_status: OrderStatus):
        allowed = _TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {self.status.value} -> {new_status.value}"
            )
        print(f"[Order] {self.status.value} -> {new_status.value}")
        self.status = new_status

    def pay(self):
        self.transition_to(OrderStatus.PAID)

    def ship(self):
        self.transition_to(OrderStatus.SHIPPED)


if __name__ == '__main__':
    order = Order()
    order.pay()
    order.ship()
    try:
        order.pay()
    except ValueError as e:
        print(f"Blocked: {e}")
