import logging
import uuid

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from tenacity import after_log
from tenacity import before_log
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_exponential_jitter

# ==========================================
# LOGGING SETUP
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

# ==========================================
# FAKE EXTERNAL API (for testing)
# ==========================================
call_count = 0


class FakePaymentAPI:
    """Simulates a flaky payment API that fails twice, then succeeds."""

    @staticmethod
    async def charge(token: str, amount: float, idempotency_key: str) -> dict:
        global call_count
        call_count += 1

        logger.info(f"[FakeAPI] Call #{call_count} | idempotency_key={idempotency_key}")

        # Fail the first 2 attempts
        if call_count <= 2:
            logger.warning(f"[FakeAPI] Simulating transient failure (attempt {call_count})")
            raise httpx.ConnectError("Network unreachable")

        # Succeed on 3rd attempt
        logger.info(f"[FakeAPI] Payment successful on attempt {call_count}")
        return {
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8]}",
            "amount": amount,
            "status": "success"
        }


# ==========================================
# RETRYABLE PAYMENT FUNCTION
# ==========================================

@retry(
    stop=stop_after_attempt(4),  # Max 4 attempts
    wait=wait_exponential_jitter(initial=1, max=10, jitter=2),  # 1s, 2s, 4s + jitter
    retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
    before=before_log(logger, logging.INFO),  # Log before each retry
    after=after_log(logger, logging.INFO),  # Log after each attempt
    reraise=True,  # Re-raise exception if all retries fail
)
async def charge_payment(token: str, amount: float, idempotency_key: str) -> dict:
    """
    Charge a payment with automatic retry on transient failures.

    Best practices:
    - Exponential backoff + jitter (prevents thundering herd)
    - Only retries on transient errors (ConnectError, Timeout)
    - Logs every attempt
    - Uses idempotency key to prevent double charges
    """
    return await FakePaymentAPI.charge(token, amount, idempotency_key)


# ==========================================
# FASTAPI ENDPOINT
# ==========================================

class PaymentRequest(BaseModel):
    token: str
    amount: float


@app.post("/payments")
async def process_payment(req: PaymentRequest):
    """
    Process a payment with retry logic.

    Idempotency: If the client retries this request (e.g., network timeout),
    they should send the same idempotency key to prevent double charges.
    """
    # Generate idempotency key (client should provide this in real apps)
    idempotency_key = str(uuid.uuid4())

    logger.info(f"[Endpoint] Processing payment | amount=${req.amount} | key={idempotency_key}")

    try:
        result = await charge_payment(
            token=req.token,
            amount=req.amount,
            idempotency_key=idempotency_key
        )

        return {
            "status": "success",
            "transaction_id": result["transaction_id"],
            "idempotency_key": idempotency_key
        }

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        # All retries failed — service is down
        logger.error(f"[Endpoint] All retries failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Payment service temporarily unavailable. Please retry later."
        )

    except Exception as e:
        # Unexpected error
        logger.exception(f"[Endpoint] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==========================================
# RUN IT
# ==========================================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
