import asyncio
import logging

import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()


# ==========================================
# BULKHEADS (Separate pools for each service)
# ==========================================

class Bulkhead:
    """
    A semaphore-based bulkhead that limits concurrent calls to a service.
    If the pool is full, new requests wait (or fail fast).
    """

    def __init__(self, name: str, max_concurrent: int, timeout: float = 5.0):
        self.name = name
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.timeout = timeout
        self.active = 0  # Track active calls for logging

    async def call(self, func, *args, **kwargs):
        """Execute a function with bulkhead protection."""
        # Try to acquire a slot (with timeout)
        try:
            await asyncio.wait_for(self.semaphore.acquire(), timeout=self.timeout)
        except asyncio.TimeoutError:
            logger.warning(f"[{self.name}] Bulkhead FULL — rejecting request")
            raise HTTPException(503, f"{self.name} service is overloaded")

        self.active += 1
        logger.info(f"[{self.name}] Acquired slot ({self.active} active)")

        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            self.semaphore.release()
            self.active -= 1
            logger.info(f"[{self.name}] Released slot ({self.active} active)")


# Create separate bulkheads for each external service
email_bulkhead = Bulkhead("Email", max_concurrent=3, timeout=2.0)
payment_bulkhead = Bulkhead("Payment", max_concurrent=5, timeout=2.0)
analytics_bulkhead = Bulkhead("Analytics", max_concurrent=2, timeout=2.0)


# ==========================================
# FAKE EXTERNAL SERVICES
# ==========================================

async def call_email_api(user_id: str) -> dict:
    """Simulates a SLOW email API (takes 5 seconds)."""
    logger.info(f"[Email API] Sending email to user {user_id}...")
    await asyncio.sleep(5)  # Slow!
    return {"status": "sent", "user_id": user_id}


async def call_payment_api(amount: float) -> dict:
    """Simulates a FAST payment API (takes 0.5 seconds)."""
    logger.info(f"[Payment API] Charging ${amount}...")
    await asyncio.sleep(0.5)  # Fast!
    return {"status": "charged", "amount": amount}


async def call_analytics_api(event: str) -> dict:
    """Simulates analytics tracking."""
    logger.info(f"[Analytics API] Tracking event: {event}")
    await asyncio.sleep(0.2)
    return {"status": "tracked", "event": event}


# ==========================================
# ENDPOINTS WITH BULKHEAD PROTECTION
# ==========================================

@app.post("/send-email/{user_id}")
async def send_email(user_id: str):
    """Send email — protected by Email bulkhead (max 3 concurrent)."""
    result = await email_bulkhead.call(call_email_api, user_id)
    return result


@app.post("/charge/{amount}")
async def charge(amount: float):
    """Charge payment — protected by Payment bulkhead (max 5 concurrent)."""
    result = await payment_bulkhead.call(call_payment_api, amount)
    return result


@app.post("/track/{event}")
async def track_event(event: str):
    """Track analytics — protected by Analytics bulkhead (max 2 concurrent)."""
    result = await analytics_bulkhead.call(call_analytics_api, event)
    return result


@app.get("/metrics")
async def metrics():
    return {
        "email": {"active": email_bulkhead.active, "max": 3},
        "payment": {"active": payment_bulkhead.active, "max": 5},
    }


# ==========================================
# TEST ENDPOINT (Simulates the problem)
# ==========================================

@app.get("/test-bulkhead")
async def test_bulkhead():
    """
    Demonstrates the bulkhead pattern in action.

    Sends 10 concurrent requests:
    - 5 email requests (slow, will fill the Email bulkhead)
    - 5 payment requests (fast, should succeed immediately)

    Without bulkheads: all 10 compete for the same pool → payments wait for emails.
    With bulkheads: emails and payments have separate pools → payments succeed instantly.
    """
    logger.info("=" * 60)
    logger.info("TEST: Sending 5 email + 5 payment requests concurrently")
    logger.info("=" * 60)

    # Create 5 email tasks (slow)
    email_tasks = [send_email(f"user_{i}") for i in range(5)]

    # Create 5 payment tasks (fast)
    payment_tasks = [charge(10.0 * i) for i in range(1, 6)]

    # Run all 10 concurrently
    start = asyncio.get_event_loop().time()
    results = await asyncio.gather(*email_tasks, *payment_tasks, return_exceptions=True)
    duration = asyncio.get_event_loop().time() - start

    logger.info("=" * 60)
    logger.info(f"TEST COMPLETE in {duration:.2f}s")
    logger.info("=" * 60)

    # Count successes/failures
    successes = sum(1 for r in results if not isinstance(r, Exception))
    failures = sum(1 for r in results if isinstance(r, Exception))

    return {
        "total_requests": 10,
        "successes": successes,
        "failures": failures,
        "duration_seconds": round(duration, 2),
        "insight": "With bulkheads: payments complete fast even though emails are slow"
    }


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
