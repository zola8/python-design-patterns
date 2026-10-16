"""Legacy app — simulates the old monolith with 3 endpoints."""
import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Legacy Monolith")


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"source": "LEGACY", "user_id": user_id, "name": f"User {user_id}"}


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    # Old, slow implementation
    return {"source": "LEGACY", "product_id": product_id, "name": f"Old Product {product_id}"}


@app.get("/reports/{report_id}")
async def get_report(report_id: int):
    return {"source": "LEGACY", "report_id": report_id, "data": "old report data"}


if __name__ == '__main__':
    print("Starting Legacy Monolith... http://localhost:8081/docs")
    uvicorn.run(app, port=8081)
