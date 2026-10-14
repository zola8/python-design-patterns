import httpx
import uvicorn
from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from resiliency_reliability.circuit_breaker.core_async import AsyncCircuitBreaker
from resiliency_reliability.circuit_breaker.core_async import CircuitOpenError

app = FastAPI()


@app.exception_handler(httpx.RequestError)
async def httpx_request_error_handler(request: Request, exc: httpx.RequestError):
    # Now any ConnectError, TimeoutException, etc. anywhere in your app automatically becomes a clean 502 instead of a raw 500.
    return JSONResponse(
        status_code=502,
        content={"error": "Upstream service unreachable", "detail": type(exc).__name__},
    )


# 1. Initialize the breaker (One per external service!)
payments_breaker = AsyncCircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30.0,
    expected_exceptions=(
        httpx.ConnectError,  # DNS / connection refused
        httpx.TimeoutException,  # Timeouts
        httpx.NetworkError,  # Other transport errors
    ),
)


def get_payments_breaker() -> AsyncCircuitBreaker:
    # In production, you might fetch this from a registry or config
    return payments_breaker


# 2. The actual async function that calls the external API
async def call_payment_gateway(token: str, amount: float):
    # ALWAYS use an async client and set a timeout in FastAPI
    async with httpx.AsyncClient(timeout=2.0) as client:
        response = await client.post(
            "https://api.fake.com/v1/charges",  # Fake endpoint
            json={"token": token, "amount": amount}
        )
        # If it's a 5xx error, raise it so the breaker catches it
        response.raise_for_status()
        return response.json()


# 3. The FastAPI Endpoint

@app.post("/checkout")
async def checkout(token: str, amount: float):
    try:
        result = await payments_breaker.call(call_payment_gateway, token, amount)
        return {"status": "success", "data": result}

    except CircuitOpenError:
        # Breaker is OPEN — fail fast
        return JSONResponse(
            status_code=503,
            content={"error": "Payment service is temporarily unavailable."},
            headers={"Retry-After": str(int(payments_breaker.recovery_timeout))},
        )

    except httpx.HTTPStatusError as e:
        if e.response.status_code >= 500:
            raise  # Let FastAPI handle 5xx as 500 (or re-raise to trip breaker)
        return JSONResponse(
            status_code=400,
            content={"error": f"Payment rejected: {e.response.status_code}"}
        )

    except httpx.RequestError as e:
        # Network-level failure: DNS, connection refused, timeout, etc.
        # The breaker has already recorded this as a failure.
        # Return a clean 502 Bad Gateway instead of a raw 500.
        return JSONResponse(
            status_code=502,
            content={
                "error": "Could not reach payment service.",
                "detail": str(e),  # Remove in production — don't leak internals
            }
        )


@app.post("/checkout-v2")
async def checkout_v2(
    token: str,
    amount: float,
    breaker: AsyncCircuitBreaker = Depends(get_payments_breaker)
):
    try:
        result = await breaker.call(call_payment_gateway, token, amount)
        return {"status": "success"}
    except CircuitOpenError:
        raise HTTPException(status_code=503, detail="Service Unavailable")


if __name__ == '__main__':
    print("http://localhost:8080/docs")
    uvicorn.run(app, port=8080)
