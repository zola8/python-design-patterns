import time

import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi import Response

app = FastAPI()


# ==========================================
# MIDDLEWARE AS CHAIN OF RESPONSIBILITY
# ==========================================

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """First handler in the chain."""
    start_time = time.time()
    print(f"[Logging] {request.method} {request.url.path}")

    # Pass to next middleware (or endpoint if this is the last one)
    response = await call_next(request)

    duration = time.time() - start_time
    print(f"[Logging] Completed in {duration:.3f}s")
    return response


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Second handler in the chain."""
    token = request.headers.get("Authorization")

    if not token:
        return Response(
            content='{"error": "Unauthorized"}',
            status_code=401,
            media_type="application/json"
        )

    print("[Auth] OK Token present")

    # Pass to next middleware
    return await call_next(request)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Third handler in the chain."""
    # Simplified rate limiting
    print("[RateLimit] OK")
    return await call_next(request)


# ==========================================
# ENDPOINT (The final handler)
# ==========================================
@app.get("/protected")
async def protected_route():
    """This is the end of the chain — the actual business logic."""
    print("[Endpoint] OK Processing request")
    return {"message": "Welcome to the protected resource"}


# ==========================================
# USAGE
# ==========================================
if __name__ == '__main__':
    uvicorn.run(app, port=8080)
    # curl http://localhost:8080/protected -H "Authorization: Bearer token"
