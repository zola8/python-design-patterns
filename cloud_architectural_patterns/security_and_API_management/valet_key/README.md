# The Valet Key Pattern

The Valet Key Pattern is about giving clients a temporary, restricted-access token to interact directly with a storage
service (like S3), bypassing your application server entirely.

Think of a valet key for a car: you give it to the parking attendant so they can move the car, but it can't open the
glove box or trunk. It's limited, temporary, and revocable.

### The Architecture

```
1. User → Your FastAPI Server: "I want to upload a file"
2. Your Server → AWS S3: "Generate a temporary upload URL for user X"
3. AWS S3 → Your Server: "Here's a pre-signed URL (valid for 10 min)"
4. Your Server → User: "Upload directly to this URL"
5. User → AWS S3: Uploads file DIRECTLY (bypassing your server!)
6. AWS S3 → User: "Upload complete"
```

```
┌─────────────────────────────────────────────────────────────┐
│  1. Client asks for upload permission                       │
│     POST /upload-url  →  Your FastAPI Server                │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Server validates user, generates valet key              │
│     - Checks auth (JWT, API key)                            │
│     - Checks quota (user can upload 100MB max)              │
│     - Asks S3 for pre-signed URL                            │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Server returns pre-signed URL to client                 │
│     {"upload_url": "https://s3.../file?signature=abc..."}   │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Client uploads DIRECTLY to S3                           │
│     PUT https://s3.../file?signature=abc...                 │
│     (Your server is NOT involved!)                          │
└─────────────────────────────────────────────────────────────┘
```
