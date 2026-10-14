from contextlib import asynccontextmanager

import uvicorn
from fastapi import BackgroundTasks
from fastapi import FastAPI


# ==========================================
# 1. THE EVENT BUS (Observer pattern)
# ==========================================
class EventBus:
    def __init__(self):
        self._handlers = {}

    def subscribe(self, event_type: str, handler: callable):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event_type: str, data: dict):
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                await handler(data)


event_bus = EventBus()


# ==========================================
# 2. THE OBSERVERS (Handlers)
# ==========================================
async def send_email_handler(data: dict):
    print(f"[Email] Sending welcome email to {data['email']}")


async def log_analytics_handler(data: dict):
    print(f"[Analytics] User {data['user_id']} registered")


async def notify_slack_handler(data: dict):
    print(f"[Slack] New user: {data['email']}")


# ==========================================
# 3. THE LIFESPAN (Modern startup/shutdown)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Register observers
    print("[Lifespan] Starting up — registering event handlers...")
    event_bus.subscribe("user_registered", send_email_handler)
    event_bus.subscribe("user_registered", log_analytics_handler)
    event_bus.subscribe("user_registered", notify_slack_handler)

    # You can also initialize databases, caches, connections here

    yield  # App runs here

    # SHUTDOWN: Cleanup
    print("[Lifespan] Shutting down — cleaning up...")


# ==========================================
# 4. THE FASTAPI APP
# ==========================================
app = FastAPI(lifespan=lifespan)


@app.post("/register")
async def register_user(email: str, background_tasks: BackgroundTasks):
    user_id = "USER-123"

    # Publish event — observers handle the rest
    background_tasks.add_task(
        event_bus.publish,
        "user_registered",
        {"user_id": user_id, "email": email}
    )

    return {
        "message": "User registered",
        "user_id": user_id,
        "email": email
    }


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
