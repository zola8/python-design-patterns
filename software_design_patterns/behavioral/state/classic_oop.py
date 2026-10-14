from abc import ABC
from abc import abstractmethod


# ==========================================
# 1. THE CONTEXT (The object that changes behavior)
# ==========================================
class Order:
    def __init__(self):
        # Start in Pending state
        self._state: OrderState = PendingState()

    def set_state(self, state: 'OrderState'):
        self._state = state
        print(f"[Order] State changed to: {state.__class__.__name__}")

    # Delegate all actions to the current state
    def pay(self):
        self._state.pay(self)

    def ship(self):
        self._state.ship(self)

    def deliver(self):
        self._state.deliver(self)

    def cancel(self):
        self._state.cancel(self)

    def refund(self):
        self._state.refund(self)


# ==========================================
# 2. THE STATE INTERFACE
# ==========================================
class OrderState(ABC):
    @abstractmethod
    def pay(self, order: Order): pass

    @abstractmethod
    def ship(self, order: Order): pass

    @abstractmethod
    def deliver(self, order: Order): pass

    @abstractmethod
    def cancel(self, order: Order): pass

    @abstractmethod
    def refund(self, order: Order): pass


# ==========================================
# 3. CONCRETE STATES (Each knows valid transitions)
# ==========================================
class PendingState(OrderState):
    def pay(self, order: Order):
        print("[Pending] Processing payment...")
        order.set_state(PaidState())

    def ship(self, order: Order):
        raise ValueError("[Pending] Cannot ship — order not paid yet!")

    def deliver(self, order: Order):
        raise ValueError("[Pending] Cannot deliver — order not paid yet!")

    def cancel(self, order: Order):
        print("[Pending] Order cancelled.")
        order.set_state(CancelledState())

    def refund(self, order: Order):
        raise ValueError("[Pending] Nothing to refund — no payment yet!")


class PaidState(OrderState):
    def pay(self, order: Order):
        raise ValueError("[Paid] Already paid!")

    def ship(self, order: Order):
        print("[Paid] Preparing shipment...")
        order.set_state(ShippedState())

    def deliver(self, order: Order):
        raise ValueError("[Paid] Cannot deliver — not shipped yet!")

    def cancel(self, order: Order):
        print("[Paid] Cancelling paid order — initiating refund...")
        order.set_state(RefundedState())

    def refund(self, order: Order):
        print("[Paid] Processing refund...")
        order.set_state(RefundedState())


class ShippedState(OrderState):
    def pay(self, order: Order):
        raise ValueError("[Shipped] Already paid!")

    def ship(self, order: Order):
        raise ValueError("[Shipped] Already shipped!")

    def deliver(self, order: Order):
        print("[Shipped] Out for delivery...")
        order.set_state(DeliveredState())

    def cancel(self, order: Order):
        raise ValueError("[Shipped] Cannot cancel — already shipped!")

    def refund(self, order: Order):
        raise ValueError("[Shipped] Cannot refund until delivered or returned.")


class DeliveredState(OrderState):
    def pay(self, order: Order):
        raise ValueError("[Delivered] Already paid!")

    def ship(self, order: Order):
        raise ValueError("[Delivered] Already delivered!")

    def deliver(self, order: Order):
        raise ValueError("[Delivered] Already delivered!")

    def cancel(self, order: Order):
        raise ValueError("[Delivered] Cannot cancel — already delivered!")

    def refund(self, order: Order):
        print("[Delivered] Processing return and refund...")
        order.set_state(RefundedState())


class CancelledState(OrderState):
    """Terminal state — no transitions allowed."""

    def _deny(self, action: str):
        raise ValueError(f"[Cancelled] Cannot {action} — order is cancelled.")

    def pay(self, order: Order): self._deny("pay")

    def ship(self, order: Order): self._deny("ship")

    def deliver(self, order: Order): self._deny("deliver")

    def cancel(self, order: Order): self._deny("cancel")

    def refund(self, order: Order): self._deny("refund")


class RefundedState(OrderState):
    """Terminal state — no transitions allowed."""

    def _deny(self, action: str):
        raise ValueError(f"[Refunded] Cannot {action} — order is refunded.")

    def pay(self, order: Order): self._deny("pay")

    def ship(self, order: Order): self._deny("ship")

    def deliver(self, order: Order): self._deny("deliver")

    def cancel(self, order: Order): self._deny("cancel")

    def refund(self, order: Order): self._deny("refund")


# ==========================================
# 4. USAGE
# ==========================================
if __name__ == "__main__":
    order = Order()

    print("=== Happy Path ===")
    order.pay()  # Pending → Paid
    order.ship()  # Paid → Shipped
    order.deliver()  # Shipped → Delivered

    print("\n=== Invalid Transition ===")
    try:
        order.pay()  # Should fail — already delivered
    except ValueError as e:
        print(f"Error: {e}")

    print("\n=== Cancellation Path ===")
    order2 = Order()
    order2.pay()  # Pending → Paid
    order2.cancel()  # Paid → Refunded (auto-refund on cancel)
