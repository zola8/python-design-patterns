from abc import ABC
from abc import abstractmethod
from typing import Optional


# ==========================================
# 1. THE HANDLER INTERFACE
# ==========================================
class Handler(ABC):
    """
    Each handler can either:
    - Handle the request and return a response
    - Pass it to the next handler
    """

    def __init__(self):
        self._next_handler: Optional[Handler] = None

    def set_next(self, handler: "Handler") -> "Handler":
        """Link handlers together."""
        self._next_handler = handler
        return handler  # Return the handler for chaining

    @abstractmethod
    def handle(self, request: dict) -> Optional[dict]:
        """
        Process the request.
        Return a response dict if handled, or None to pass to next handler.
        """
        pass


# ==========================================
# 2. CONCRETE HANDLERS (Each handles ONE concern)
# ==========================================
class AuthenticationHandler(Handler):
    def handle(self, request: dict) -> Optional[dict]:
        token = request.get("headers", {}).get("Authorization")

        if not token:
            return {"status": 401, "error": "Missing authentication token"}

        if not token.startswith("Bearer "):
            return {"status": 401, "error": "Invalid token format"}

        # Token is valid — pass to next handler
        print("[Auth] Token validated")
        return self._next_handler.handle(request) if self._next_handler else None


class AuthorizationHandler(Handler):
    def handle(self, request: dict) -> Optional[dict]:
        user_role = request.get("user", {}).get("role")
        required_permission = request.get("required_permission")

        # Check if user has the required permission
        permissions = {
            "admin": ["read", "write", "delete"],
            "editor": ["read", "write"],
            "viewer": ["read"],
        }

        user_perms = permissions.get(user_role, [])

        if required_permission not in user_perms:
            return {"status": 403, "error": f"Permission '{required_permission}' denied"}

        print(f"[AuthZ] User has '{required_permission}' permission")
        return self._next_handler.handle(request) if self._next_handler else None


class RateLimitHandler(Handler):
    def __init__(self, max_requests: int = 100):
        super().__init__()
        self.request_count = 0
        self.max_requests = max_requests

    def handle(self, request: dict) -> Optional[dict]:
        self.request_count += 1

        if self.request_count > self.max_requests:
            return {"status": 429, "error": "Rate limit exceeded"}

        print(f"[RateLimit] Request #{self.request_count}")
        return self._next_handler.handle(request) if self._next_handler else None


class ValidationHandler(Handler):
    def handle(self, request: dict) -> Optional[dict]:
        body = request.get("body", {})

        if not body:
            return {"status": 400, "error": "Request body is empty"}

        if "name" not in body:
            return {"status": 400, "error": "Missing required field: 'name'"}

        print("[Validation] Request body is valid")
        return self._next_handler.handle(request) if self._next_handler else None


class LoggingHandler(Handler):
    def handle(self, request: dict) -> Optional[dict]:
        print(f"[Logging] Request from {request.get('client_ip', 'unknown')}")
        # Logging never blocks — always pass to next handler
        return self._next_handler.handle(request) if self._next_handler else None


# ==========================================
# 3. THE FINAL HANDLER (Business Logic)
# ==========================================
class BusinessLogicHandler(Handler):
    def handle(self, request: dict) -> dict:
        """This is the end of the chain — actually process the request."""
        print("[Business] Processing request...")
        return {
            "status": 200,
            "message": f"Created resource: {request['body']['name']}"
        }


# ==========================================
# 4. BUILD THE CHAIN
# ==========================================
def build_chain() -> Handler:
    """Assemble the middleware chain."""
    auth = AuthenticationHandler()
    authz = AuthorizationHandler()
    rate_limit = RateLimitHandler(max_requests=1000)
    validation = ValidationHandler()
    logging = LoggingHandler()
    business = BusinessLogicHandler()

    # Link them: auth -> authz -> rate_limit -> validation -> logging -> business
    auth.set_next(authz).set_next(rate_limit).set_next(validation).set_next(logging).set_next(business)

    return auth  # Return the first handler in the chain


# ==========================================
# 5. USAGE
# ==========================================
if __name__ == "__main__":
    chain = build_chain()

    # Test 1: Valid request
    print("=== Test 1: Valid request ===")
    request = {
        "headers": {"Authorization": "Bearer abc123"},
        "user": {"role": "editor"},
        "required_permission": "write",
        "body": {"name": "New Article"},
        "client_ip": "192.168.1.1"
    }
    response = chain.handle(request)
    print(f"Response: {response}\n")

    # Test 2: Missing auth
    print("=== Test 2: Missing auth ===")
    request["headers"] = {}
    response = chain.handle(request)
    print(f"Response: {response}\n")

    # Test 3: Insufficient permissions
    print("=== Test 3: Insufficient permissions ===")
    request["headers"] = {"Authorization": "Bearer abc123"}
    request["user"] = {"role": "viewer"}
    request["required_permission"] = "delete"
    response = chain.handle(request)
    print(f"Response: {response}\n")

    # Test 4: Invalid body
    print("=== Test 4: Invalid body ===")
    request["user"] = {"role": "editor"}
    request["required_permission"] = "write"
    request["body"] = {}  # Missing 'name'
    response = chain.handle(request)
    print(f"Response: {response}")
