"""New Products service — the migrated microservice."""
import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Products Service")


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    # New, fast implementation with better data
    return {
        "source": "NEW",
        "product_id": product_id,
        "name": f"New Product {product_id}",
        "price": 99.99,
        "in_stock": True,
        "rating": 4.5,
    }


@app.get("/products")
async def list_products():
    return {
        "source": "NEW",
        "products": [
            {"id": 1, "name": "Laptop", "price": 999},
            {"id": 2, "name": "Mouse", "price": 29},
        ],
    }


if __name__ == '__main__':
    print("Starting Legacy Monolith... http://localhost:8082/docs")
    uvicorn.run(app, port=8082)
