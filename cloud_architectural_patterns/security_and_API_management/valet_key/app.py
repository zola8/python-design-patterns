"""
Valet Key Pattern — Swagger-testable version.
"""
import time

import httpx
import uvicorn
from fastapi import Depends
from fastapi import FastAPI
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from pydantic import BaseModel

app = FastAPI(
    title="Valet Key Pattern",
    description="Test the valet key pattern directly in Swagger UI"
)

MOCK_S3_URL = "http://localhost:8081"

# Fake user database
USERS = {
    "alice-token": {"user_id": "user-123", "name": "Alice", "quota_bytes": 100 * 1024 * 1024},
    "bob-token": {"user_id": "user-456", "name": "Bob", "quota_bytes": 50 * 1024 * 1024},
}

security = HTTPBearer()


# ==========================================
# AUTH
# ==========================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Validate token and return user info."""
    token = credentials.credentials

    if token not in USERS:
        raise HTTPException(401, "Invalid token. Use 'alice-token' or 'bob-token'")

    return USERS[token]


# ==========================================
# REAL-WORLD ENDPOINTS (For production use)
# ==========================================

class UploadUrlRequest(BaseModel):
    filename: str
    content_type: str = "application/octet-stream"


class UploadUrlResponse(BaseModel):
    upload_url: str
    expires_at: float
    max_size_bytes: int
    file_key: str


@app.post("/upload-url", response_model=UploadUrlResponse, tags=["Real-World"])
async def get_upload_url(
    req: UploadUrlRequest,
    user: dict = Depends(get_current_user),
):
    """
    Generate a pre-signed URL for direct S3 upload.

    In production, the client would:
    1. Call this endpoint to get the upload_url
    2. Upload directly to that URL (bypassing your server)
    3. Call /files/metadata to register the file
    """
    file_key = f"users/{user['user_id']}/{int(time.time())}_{req.filename}"

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            f"{MOCK_S3_URL}/generate-upload-url",
            json={
                "bucket": "my-app-uploads",
                "key": file_key,
                "expires_in_seconds": 600,
            }
        )

        if response.status_code != 200:
            raise HTTPException(500, "Failed to generate upload URL")

        s3_response = response.json()

    return UploadUrlResponse(
        upload_url=s3_response["upload_url"],
        expires_at=s3_response["expires_at"],
        max_size_bytes=min(s3_response["max_size_bytes"], user["quota_bytes"]),
        file_key=file_key,
    )


class FileMetadata(BaseModel):
    file_key: str
    filename: str
    content_type: str


@app.post("/files/metadata", tags=["Real-World"])
async def save_file_metadata(
    metadata: FileMetadata,
    user: dict = Depends(get_current_user),
):
    """Register file metadata after direct upload to S3."""
    print(f"[DB] Saving metadata for {metadata.file_key} uploaded by {user['user_id']}")

    return {
        "status": "saved",
        "file_key": metadata.file_key,
        "uploaded_by": user["user_id"],
    }


# ==========================================
# SWAGGER-TESTABLE ENDPOINT (Demo)
# ==========================================

@app.post("/test-valet-key", tags=["Swagger Demo"])
async def test_valet_key(
    file: UploadFile = File(..., description="File to upload"),
    user: dict = Depends(get_current_user),
):
    """
    **DEMO ENDPOINT** — Simulates the entire valet key flow in one call.

    This endpoint:
    1. Generates a valet key (pre-signed URL)
    2. Uploads the file directly to mock S3
    3. Registers the metadata

    In production, steps 2-3 would be done by the client directly.
    This is just for testing in Swagger UI.
    """
    # Step 1: Generate valet key
    file_key = f"users/{user['user_id']}/{int(time.time())}_{file.filename}"

    async with httpx.AsyncClient(timeout=5.0) as client:
        # Generate pre-signed URL
        url_response = await client.post(
            f"{MOCK_S3_URL}/generate-upload-url",
            json={
                "bucket": "my-app-uploads",
                "key": file_key,
                "expires_in_seconds": 600,
            }
        )

        if url_response.status_code != 200:
            raise HTTPException(500, "Failed to generate upload URL")

        s3_data = url_response.json()
        upload_url = s3_data["upload_url"]
        signature = s3_data["signature"]

        # Step 2: Upload file directly to S3 (simulating client behavior)
        file_content = await file.read()

        upload_response = await client.put(
            upload_url,
            content=file_content,
            headers={"Content-Type": file.content_type or "application/octet-stream"},
        )

        if upload_response.status_code != 200:
            raise HTTPException(500, "Failed to upload to S3")

        upload_result = upload_response.json()

    # Step 3: Register metadata (simulating client callback)
    metadata = {
        "file_key": file_key,
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(file_content),
    }

    return {
        "message": "Valet Key pattern demonstrated successfully!",
        "flow": {
            "step_1_generate_key": {
                "description": "Server generates pre-signed URL",
                "upload_url": upload_url,
                "expires_at": s3_data["expires_at"],
            },
            "step_2_direct_upload": {
                "description": "Client uploads directly to S3 (bypassing server)",
                "result": upload_result,
            },
            "step_3_register_metadata": {
                "description": "Client registers file in database",
                "metadata": metadata,
            },
        },
        "summary": {
            "user": user["name"],
            "file_key": file_key,
            "file_size": len(file_content),
            "server_bandwidth_saved": "100% (file went directly to S3)",
        },
    }


# ==========================================
# DOWNLOAD ENDPOINT (For verification)
# ==========================================

@app.get("/download/{file_key:path}", tags=["Swagger Demo"])
async def download_file(
    file_key: str,
    user: dict = Depends(get_current_user),
):
    """Download a file from mock S3 (for testing)."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{MOCK_S3_URL}/download/my-app-uploads/{file_key}")

        if response.status_code == 404:
            raise HTTPException(404, "File not found")

        return Response(
            content=response.content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={file_key.split('/')[-1]}"}
        )


if __name__ == '__main__':
    print('http://localhost:8080/docs')
    uvicorn.run(app, host="0.0.0.0", port=8080)
