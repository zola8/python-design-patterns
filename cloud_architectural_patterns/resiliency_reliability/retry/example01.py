import httpx
import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_exponential_jitter

app = FastAPI()


# ==========================================
# RETRYABLE HTTP CLIENT
# ==========================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10, jitter=2),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
    reraise=True,
)
async def call_external_api(url: str, data: dict) -> dict:
    """Call an external API with automatic retry on transient failures."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(url, json=data)

        # Only retry on 5xx (transient) — 4xx are permanent
        if response.status_code >= 500:
            response.raise_for_status()

        return response.json()


# ==========================================
# ENDPOINT
# ==========================================

class PaymentRequest(BaseModel):
    token: str
    amount: float


@app.post("/payments")
async def process_payment(req: PaymentRequest):
    """Process a payment with automatic retry."""
    try:
        result = await call_external_api(
            "https://api.fake.com/v1/charges",
            {"token": req.token, "amount": req.amount}
        )
        return {"status": "success", "transaction_id": result["id"]}

    except httpx.HTTPStatusError as e:
        # 4xx error — permanent failure, don't retry
        raise HTTPException(400, f"Payment rejected: {e.response.status_code}")

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        # All retries failed — service is down
        raise HTTPException(503, "Payment service temporarily unavailable")


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
