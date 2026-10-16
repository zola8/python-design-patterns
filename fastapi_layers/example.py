"""
FastAPI Order API — with proper email + observer + circuit breaker wiring.
"""
from abc import ABC
from abc import abstractmethod
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from pydantic import BaseModel


# ==========================================
# DOMAIN LAYER
# ==========================================

class Order:
    def __init__(self, order_id: str, customer: str, total: float, status: str = "pending"):
        self.order_id = order_id
        self.customer = customer
        self.total = total
        self.status = status


class OrderRepository(ABC):
    @abstractmethod
    async def save(self, order: Order) -> None: ...

    @abstractmethod
    async def get(self, order_id: str) -> Order | None: ...


class EmailSender(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None: ...


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list] = {}

    def subscribe(self, event: str, handler):
        self._handlers.setdefault(event, []).append(handler)

    async def publish(self, event: str, data: dict):
        for handler in self._handlers.get(event, []):
            await handler(data)


class OrderService:
    def __init__(self, repo: OrderRepository, events: EventBus):
        self.repo = repo
        self.events = events
        self._counter = 0

    async def create_order(self, customer: str, total: float) -> str:
        self._counter += 1
        order = Order(f"ORD-{self._counter:04d}", customer, total)
        await self.repo.save(order)

        # Publish event — observers handle side effects
        await self.events.publish("order.created", {
            "order_id": order.order_id,
            "customer": customer,
            "total": total,
        })

        return order.order_id

    async def get_order(self, order_id: str) -> Order | None:
        return await self.repo.get(order_id)


# ==========================================
# INFRASTRUCTURE LAYER
# ==========================================

class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._orders: dict[str, Order] = {}

    async def save(self, order: Order) -> None:
        self._orders[order.order_id] = order

    async def get(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)


class FakeEmailSender(EmailSender):
    async def send(self, to: str, subject: str, body: str) -> None:
        print(f"[Email] Sent to {to} | Subject: {subject}")


class CircuitBreakerEmailSender(EmailSender):
    """Wraps another EmailSender with circuit breaker protection."""

    def __init__(self, inner: EmailSender, threshold: int = 3):
        self.inner = inner
        self.threshold = threshold
        self.failures = 0
        self.is_open = False

    async def send(self, to: str, subject: str, body: str) -> None:
        if self.is_open:
            print("[CircuitBreaker] OPEN — skipping email send")
            return
        try:
            await self.inner.send(to, subject, body)
            self.failures = 0  # Reset on success
        except Exception as e:
            self.failures += 1
            print(f"[CircuitBreaker] Failure #{self.failures}: {e}")
            if self.failures >= self.threshold:
                self.is_open = True
                print(f"[CircuitBreaker] TRIPPED after {self.failures} failures")
            raise


# ==========================================
# OBSERVER HANDLER (Now actually sends email!)
# ==========================================

class OrderCreatedHandler:
    """Observer that sends confirmation email when order is created."""

    def __init__(self, email_sender: EmailSender):
        self.email_sender = email_sender

    async def __call__(self, data: dict):
        """Called by EventBus when order.created is published."""
        print(f"[Observer] 📨 Sending confirmation email for order {data['order_id']}...")

        await self.email_sender.send(
            to=data["customer"],
            subject=f"Order {data['order_id']} Confirmed",
            body=f"Thank you! Your order total is ${data['total']:.2f}"
        )


# ==========================================
# SCHEMAS
# ==========================================

class CreateOrderRequest(BaseModel):
    customer: str
    total: float


class OrderResponse(BaseModel):
    order_id: str
    customer: str
    total: float
    status: str


# ==========================================
# PRESENTATION LAYER
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Wire everything together
    print("[Lifespan] Starting up...")

    # Infrastructure
    repo = InMemoryOrderRepository()
    email = CircuitBreakerEmailSender(FakeEmailSender())

    # Event bus with observer
    events = EventBus()
    order_handler = OrderCreatedHandler(email)
    events.subscribe("order.created", order_handler)

    # Service (no longer needs email — observer handles it)
    service = OrderService(repo=repo, events=events)

    app.state.service = service
    print("[Lifespan] App started")

    yield

    print("[Lifespan] App shutting down")


app = FastAPI(lifespan=lifespan)


def get_service(request: Request) -> OrderService:
    return request.app.state.service


@app.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    req: CreateOrderRequest,
    service: OrderService = Depends(get_service),
):
    order_id = await service.create_order(req.customer, req.total)
    order = await service.get_order(order_id)
    return OrderResponse(
        order_id=order.order_id,
        customer=order.customer,
        total=order.total,
        status=order.status,
    )


@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    service: OrderService = Depends(get_service),
):
    order = await service.get_order(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return OrderResponse(
        order_id=order.order_id,
        customer=order.customer,
        total=order.total,
        status=order.status,
    )


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
