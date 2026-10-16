import uvicorn
from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel

app = FastAPI()

# ==========================================
# FAKE DATABASE (in-memory)
# ==========================================
fake_db = {
    "posts": {
        1: {"id": 1, "title": "Hello World", "content": "My first post"},
        2: {"id": 2, "title": "CQRS is Cool", "content": "Let me explain..."},
    },
    "comments": [
        # Each comment: {id, post_id, text, author}
    ],
}
comment_counter = 0


# ==========================================
# WRITE MODEL (Commands)
# ==========================================
class BlogWriteModel:
    """Normalized for writes — separate tables, strict operations."""

    def add_comment(self, post_id: int, text: str, author: str) -> int:
        global comment_counter
        comment_counter += 1

        # Validate post exists
        if post_id not in fake_db["posts"]:
            raise ValueError(f"Post {post_id} not found")

        # Insert into comments table (normalized)
        comment = {
            "id": comment_counter,
            "post_id": post_id,
            "text": text,
            "author": author,
        }
        fake_db["comments"].append(comment)
        return comment_counter


# ==========================================
# READ MODEL (Queries)
# ==========================================
class BlogReadModel:
    """Denormalized for reads — pre-joined, optimized for specific queries."""

    def get_post_with_comments(self, post_id: int) -> dict:
        post = fake_db["posts"].get(post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found")

        # Denormalized view: post + all its comments in one structure
        comments = [c for c in fake_db["comments"] if c["post_id"] == post_id]

        return {
            "id": post["id"],
            "title": post["title"],
            "content": post["content"],
            "comments": comments,  # Embedded — no JOIN needed at read time
        }

    def list_all_posts_with_comment_counts(self) -> list[dict]:
        """Another read-optimized query — different shape than the write model."""
        result = []
        for post in fake_db["posts"].values():
            count = sum(1 for c in fake_db["comments"] if c["post_id"] == post["id"])
            result.append({
                "id": post["id"],
                "title": post["title"],
                "comment_count": count,
            })
        return result


# ==========================================
# DEPENDENCY FUNCTIONS (the "get_*" functions)
# ==========================================
def get_write_model() -> BlogWriteModel:
    """FastAPI calls this to inject the write model."""
    return BlogWriteModel()


def get_read_model() -> BlogReadModel:
    """FastAPI calls this to inject the read model."""
    return BlogReadModel()


# ==========================================
# ENDPOINTS
# ==========================================
class CommentRequest(BaseModel):
    text: str
    author: str


@app.post("/posts/{post_id}/comments")
def add_comment(
    post_id: int,
    req: CommentRequest,
    write_model: BlogWriteModel = Depends(get_write_model),  # ← Injected!
):
    """Command: Write operation."""
    try:
        comment_id = write_model.add_comment(post_id, req.text, req.author)
        return {"comment_id": comment_id, "status": "added"}
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.get("/posts/{post_id}")
def get_post(
    post_id: int,
    read_model: BlogReadModel = Depends(get_read_model),  # ← Injected!
):
    """Query: Read operation — returns denormalized view."""
    try:
        return read_model.get_post_with_comments(post_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.get("/posts")
def list_posts(
    read_model: BlogReadModel = Depends(get_read_model),
):
    """Another query — different read shape."""
    return read_model.list_all_posts_with_comment_counts()


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
