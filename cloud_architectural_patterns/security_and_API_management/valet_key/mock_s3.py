"""Mock S3 service — simulates AWS S3 pre-signed URLs."""
import secrets
import time

import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import Response
from pydantic import BaseModel

app = FastAPI(title="Mock S3")

# In-memory storage
storage: dict[str, bytes] = {}
issued_signatures: dict[str, dict] = {}


class GenerateUrlRequest(BaseModel):
    bucket: str
    key: str
    expires_in_seconds: int = 600


@app.post("/generate-upload-url")
async def generate_upload_url(req: GenerateUrlRequest):
    """Generate a pre-signed URL for uploading."""
    signature = secrets.token_urlsafe(32)

    issued_signatures[signature] = {
        "bucket": req.bucket,
        "key": req.key,
        "expires_at": time.time() + req.expires_in_seconds,
        "max_size_bytes": 100 * 1024 * 1024,
    }

    upload_url = f"http://localhost:8081/upload/{req.bucket}/{req.key}?signature={signature}"

    return {
        "upload_url": upload_url,
        "expires_at": issued_signatures[signature]["expires_at"],
        "signature": signature,  # Include for testing
    }


@app.put("/upload/{bucket}/{key:path}")
async def upload_file(
    bucket: str,
    key: str,
    request: Request,
    signature: str,
):
    """Upload a file using a pre-signed URL."""
    if signature not in issued_signatures:
        raise HTTPException(403, "Invalid signature")

    sig_data = issued_signatures[signature]

    if time.time() > sig_data["expires_at"]:
        raise HTTPException(403, "Signature expired")

    if sig_data["bucket"] != bucket or sig_data["key"] != key:
        raise HTTPException(403, "Signature doesn't match this path")

    body = await request.body()

    if len(body) > sig_data["max_size_bytes"]:
        raise HTTPException(413, f"File too large")

    storage[f"{bucket}/{key}"] = body
    del issued_signatures[signature]

    return {
        "status": "uploaded",
        "bucket": bucket,
        "key": key,
        "size_bytes": len(body),
    }


@app.get("/download/{bucket}/{key:path}")
async def download_file(bucket: str, key: str):
    """Download a file."""
    path = f"{bucket}/{key}"
    if path not in storage:
        raise HTTPException(404, "File not found")

    return Response(content=storage[path], media_type="application/octet-stream")


if __name__ == '__main__':
    print('http://localhost:8081/docs')
    uvicorn.run(app, host="0.0.0.0", port=8081)
