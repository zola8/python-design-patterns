"""
API Gateway — the "strangler fig" that routes traffic
between the new microservice and the legacy monolith.
"""
import httpx
import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Strangler Fig Gateway",
    description="Routes traffic between new microservices and legacy monolith"
)

# Service registry
LEGACY_URL = "http://localhost:8081"
NEW_PRODUCTS_URL = "http://localhost:8082"


def route_request(path: str) -> str:
    """
    Routing rules — this is where the strangulation happens.
    Currently: only /products/* goes to the new service.
    Everything else still goes to the legacy monolith.
    """
    if path.startswith("products"):
        return NEW_PRODUCTS_URL  # Migrated
    else:
        return LEGACY_URL  # Still legacy


# ==========================================
# SHARED FORWARDING LOGIC
# ==========================================

async def forward_request(request: Request, path: str):
    """Forward the request to the appropriate service."""
    target = route_request(path)
    url = f"{target}/{path}"

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                params=request.query_params,
                headers={k: v for k, v in request.headers.items() if k != "host"},
            )

            # Add a header so we can see which service handled it
            served_by = "New" if target == NEW_PRODUCTS_URL else "Legacy"
            headers = {"X-Served-By": served_by}

            return JSONResponse(
                status_code=response.status_code,
                content=response.json(),
                headers=headers,
            )
        except httpx.ConnectError:
            raise HTTPException(503, f"Service at {target} is down")


# ==========================================
# TEST ENDPOINT (Demonstrates the pattern)
# ==========================================

@app.get("/test", operation_id="test_strangler")
async def test_strangler():
    """
    Test endpoint that acts like an external client.
    It ONLY talks to the Gateway.
    The Gateway handles the routing and adds the 'X-Served-By' header.
    """
    # The Gateway's URL (this is all the client should know)
    GATEWAY_URL = "http://localhost:8080"

    async with httpx.AsyncClient(timeout=5.0) as client:
        results = {}

        test_cases = [
            ("users", "users/42"),
            ("products", "products/1"),
            ("reports", "reports/7"),
        ]

        for name, path in test_cases:
            try:
                resp = await client.get(f"{GATEWAY_URL}/{path}")

                # Read the header the Gateway added to prove routing worked
                served_by = resp.headers.get("X-Served-By", "Unknown")

                results[name] = {
                    "path": f"/{path}",
                    "served_by": served_by,
                    "status_code": resp.status_code,
                    "response": resp.json(),
                }
            except Exception as e:
                results[name] = {
                    "path": f"/{path}",
                    "error": str(e),
                }

    return {
        "message": "Strangler Fig Pattern in Action",
        "summary": {
            "new_service": sum(1 for r in results.values() if "New" in r.get("served_by", "")),
            "legacy": sum(1 for r in results.values() if "Legacy" in r.get("served_by", "")),
        },
        "details": results,
    }


# ==========================================
# ADMIN ENDPOINT (Migration status)
# ==========================================

@app.get("/admin/migration-status", operation_id="migration_status")
async def migration_status():
    """Show the migration progress."""
    return {
        "migrated": [
            {"path": "/products/*", "status": "Live on new service"},
        ],
        "still_legacy": [
            {"path": "/users/*", "status": "Legacy"},
            {"path": "/reports/*", "status": "Legacy"},
        ],
        "next": "Migrate /users/* to User Service",
    }


# ==========================================
# SEPARATE ROUTES PER METHOD (fixes duplicate operation ID warning)
# ==========================================

@app.get("/{path:path}", operation_id="gateway_get")
async def gateway_get(request: Request, path: str):
    """Forward GET requests to the appropriate service."""
    return await forward_request(request, path)


@app.post("/{path:path}", operation_id="gateway_post")
async def gateway_post(request: Request, path: str):
    """Forward POST requests to the appropriate service."""
    return await forward_request(request, path)


@app.put("/{path:path}", operation_id="gateway_put")
async def gateway_put(request: Request, path: str):
    """Forward PUT requests to the appropriate service."""
    return await forward_request(request, path)


@app.delete("/{path:path}", operation_id="gateway_delete")
async def gateway_delete(request: Request, path: str):
    """Forward DELETE requests to the appropriate service."""
    return await forward_request(request, path)


if __name__ == '__main__':
    print("http://localhost:8080/docs")
    uvicorn.run(app, port=8080)
