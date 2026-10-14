from typing import Callable
from typing import Optional

HandlerFunc = Callable[[dict], Optional[dict]]


def authentication_handler(request: dict, next_handler: HandlerFunc) -> Optional[dict]:
    if not request.get("headers", {}).get("Authorization"):
        return {"status": 401, "error": "Unauthorized"}
    print("[Auth] OK")
    return next_handler(request)


def authorization_handler(request: dict, next_handler: HandlerFunc) -> Optional[dict]:
    if request["user"]["role"] == "viewer" and request["required_permission"] == "delete":
        return {"status": 403, "error": "Forbidden"}
    print("[AuthZ] OK")
    return next_handler(request)


# FIX: Terminal handler only takes request — no next_handler
def final_handler(request: dict) -> dict:
    """End of chain — actually processes the request."""
    print("[Business] OK")
    return {"status": 200, "message": "Success"}


# Build the chain
chain = lambda req: authentication_handler(
    req,
    lambda req: authorization_handler(
        req,
        final_handler
    )
)

if __name__ == '__main__':
    request = {
        "headers": {"Authorization": "Bearer token"},
        "user": {"role": "editor"},
        "required_permission": "write"
    }

    response = chain(request)
    print(response)
