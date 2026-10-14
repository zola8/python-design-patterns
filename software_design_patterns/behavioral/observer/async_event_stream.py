import asyncio
from typing import AsyncGenerator


class AsyncOrderService:
    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        """Each subscriber gets their own queue."""
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    async def place_order(self, user_email: str, total: float):
        order = {"id": "ORD-456", "user_email": user_email, "total": total}
        print(f"[OrderService] Order placed: {order['id']}")

        # Notify all subscribers
        for queue in self._subscribers:
            await queue.put(order)

    async def order_stream(self, queue: asyncio.Queue) -> AsyncGenerator[dict, None]:
        """Async generator that yields orders from a pre-subscribed queue."""
        while True:
            order = await queue.get()
            yield order


async def main():
    service = AsyncOrderService()

    # Subscriber 1: Email service
    async def email_handler(queue: asyncio.Queue):
        async for order in service.order_stream(queue):
            print(f"[Email] Sending to {order['user_email']}")

    # Subscriber 2: Analytics
    async def analytics_handler(queue: asyncio.Queue):
        async for order in service.order_stream(queue):
            print(f"[Analytics] Tracking {order['id']}")

    email_queue = service.subscribe()
    analytics_queue = service.subscribe()

    # Now start the tasks
    asyncio.create_task(email_handler(email_queue))
    asyncio.create_task(analytics_handler(analytics_queue))

    # Give tasks a moment to start (optional but safe)
    await asyncio.sleep(0.1)

    # Place orders — now subscribers exist!
    await service.place_order("alice@example.com", 100.0)
    await service.place_order("bob@example.com", 200.0)

    # Let tasks process the messages
    await asyncio.sleep(0.1)


if __name__ == '__main__':
    asyncio.run(main())
