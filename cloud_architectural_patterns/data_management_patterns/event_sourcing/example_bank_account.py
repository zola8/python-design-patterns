"""
Event Sourcing Pattern — Bank Account Example
Store transactions as events, derive balance by replaying them.
"""
import uuid
from datetime import datetime
from typing import Literal

import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Event Sourcing",
    description="Bank account with full audit trail via event sourcing"
)


# ==========================================
# EVENT STORE (The source of truth)
# ==========================================

class Event(BaseModel):
    event_id: str
    account_id: str
    event_type: Literal["AccountOpened", "Deposited", "Withdrew", "TransferOut", "TransferIn"]
    amount: float
    timestamp: datetime
    metadata: dict = {}  # Who did it, why, correlation ID, etc.


class EventStore:
    """
    Append-only log of events.
    In production: use Kafka, EventStoreDB, PostgreSQL with append-only table.
    """

    def __init__(self):
        self._events: list[Event] = []

    def append(self, event: Event):
        """Events are NEVER modified or deleted — only appended."""
        self._events.append(event)

    def get_events(self, account_id: str, before: datetime | None = None) -> list[Event]:
        """Get all events for an account, optionally up to a point in time."""
        events = [e for e in self._events if e.account_id == account_id]
        if before:
            events = [e for e in events if e.timestamp < before]
        return events

    def all_events(self) -> list[Event]:
        return self._events


event_store = EventStore()


# ==========================================
# ACCOUNT AGGREGATE (Derived state)
# ==========================================

class Account:
    """
    The Account is built by replaying events.
    It has no direct state — only derived from events.
    """

    def __init__(self, account_id: str, events: list[Event]):
        self.account_id = account_id
        self.balance = 0.0
        self.created_at: datetime | None = None
        self.transaction_count = 0

        # Replay events to build current state
        for event in events:
            self._apply(event)

    def _apply(self, event: Event):
        """Apply a single event to update state."""
        if event.event_type == "AccountOpened":
            self.created_at = event.timestamp
            self.balance = event.amount
        elif event.event_type == "Deposited":
            self.balance += event.amount
            self.transaction_count += 1
        elif event.event_type == "Withdrew":
            self.balance -= event.amount
            self.transaction_count += 1
        elif event.event_type == "TransferOut":
            self.balance -= event.amount
            self.transaction_count += 1
        elif event.event_type == "TransferIn":
            self.balance += event.amount
            self.transaction_count += 1

    def to_dict(self) -> dict:
        return {
            "account_id": self.account_id,
            "balance": round(self.balance, 2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "transaction_count": self.transaction_count,
        }


def get_account(account_id: str, before: datetime | None = None) -> Account:
    """Reconstruct an account by replaying its events."""
    events = event_store.get_events(account_id, before=before)
    if not events:
        raise HTTPException(404, f"Account {account_id} not found")
    return Account(account_id, events)


# ==========================================
# COMMANDS (Write operations — produce events)
# ==========================================

class OpenAccountRequest(BaseModel):
    account_id: str
    initial_deposit: float = 0.0


class DepositRequest(BaseModel):
    amount: float
    description: str = ""


class WithdrawRequest(BaseModel):
    amount: float
    description: str = ""


class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float


@app.post("/accounts", status_code=201, tags=["Commands"])
async def open_account(req: OpenAccountRequest):
    """Open a new account (creates an AccountOpened event)."""
    # Check if account already exists
    existing = event_store.get_events(req.account_id)
    if existing:
        raise HTTPException(409, f"Account {req.account_id} already exists")

    event = Event(
        event_id=str(uuid.uuid4()),
        account_id=req.account_id,
        event_type="AccountOpened",
        amount=req.initial_deposit,
        timestamp=datetime.now(),
        metadata={"action": "open_account"},
    )
    event_store.append(event)

    return {"status": "created", "event": event.model_dump()}


@app.post("/accounts/{account_id}/deposit", tags=["Commands"])
async def deposit(account_id: str, req: DepositRequest):
    """Deposit money (creates a Deposited event)."""
    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    # Verify account exists
    get_account(account_id)

    event = Event(
        event_id=str(uuid.uuid4()),
        account_id=account_id,
        event_type="Deposited",
        amount=req.amount,
        timestamp=datetime.now(),
        metadata={"description": req.description},
    )
    event_store.append(event)

    account = get_account(account_id)
    return {"status": "deposited", "new_balance": account.balance, "event": event.model_dump()}


@app.post("/accounts/{account_id}/withdraw", tags=["Commands"])
async def withdraw(account_id: str, req: WithdrawRequest):
    """Withdraw money (creates a Withdrew event)."""
    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    account = get_account(account_id)

    if account.balance < req.amount:
        raise HTTPException(400, f"Insufficient funds. Balance: {account.balance}")

    event = Event(
        event_id=str(uuid.uuid4()),
        account_id=account_id,
        event_type="Withdrew",
        amount=req.amount,
        timestamp=datetime.now(),
        metadata={"description": req.description},
    )
    event_store.append(event)

    account = get_account(account_id)
    return {"status": "withdrew", "new_balance": account.balance, "event": event.model_dump()}


@app.post("/transfers", tags=["Commands"])
async def transfer(req: TransferRequest):
    """Transfer between accounts (creates TWO events — atomic)."""
    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    # Verify both accounts exist
    from_account = get_account(req.from_account)
    get_account(req.to_account)

    if from_account.balance < req.amount:
        raise HTTPException(400, "Insufficient funds")

    # Create two events (in production, use a transaction)
    timestamp = datetime.now()

    out_event = Event(
        event_id=str(uuid.uuid4()),
        account_id=req.from_account,
        event_type="TransferOut",
        amount=req.amount,
        timestamp=timestamp,
        metadata={"to": req.to_account},
    )

    in_event = Event(
        event_id=str(uuid.uuid4()),
        account_id=req.to_account,
        event_type="TransferIn",
        amount=req.amount,
        timestamp=timestamp,
        metadata={"from": req.from_account},
    )

    event_store.append(out_event)
    event_store.append(in_event)

    return {
        "status": "transferred",
        "from_balance": get_account(req.from_account).balance,
        "to_balance": get_account(req.to_account).balance,
        "events": [out_event.model_dump(), in_event.model_dump()],
    }


# ==========================================
# QUERIES (Read operations — derived from events)
# ==========================================

@app.get("/accounts/{account_id}", tags=["Queries"])
async def get_account_state(account_id: str):
    """Get current account state (derived by replaying events)."""
    account = get_account(account_id)
    return account.to_dict()


@app.get("/accounts/{account_id}/history", tags=["Queries"])
async def get_account_history(account_id: str):
    """Get full event history for an account (the audit trail)."""
    events = event_store.get_events(account_id)
    if not events:
        raise HTTPException(404, "Account not found")

    return {
        "account_id": account_id,
        "event_count": len(events),
        "events": [e.model_dump() for e in events],
    }


@app.get("/accounts/{account_id}/balance-at", tags=["Time Travel"])
async def get_balance_at(account_id: str, before: str):
    """
    TIME TRAVEL: What was the balance at a specific point in time?

    Example: ?before=2024-01-15T12:00:00
    """
    try:
        before_dt = datetime.fromisoformat(before)
    except ValueError:
        raise HTTPException(400, "Invalid datetime format. Use ISO format.")

    account = get_account(account_id, before=before_dt)
    return {
        "account_id": account_id,
        "balance_at": before,
        "balance": account.balance,
        "events_before": account.transaction_count,
    }


@app.get("/events", tags=["Audit"])
async def get_all_events():
    """Get ALL events in the system (global audit log)."""
    return {
        "total_events": len(event_store._events),
        "events": [e.model_dump() for e in event_store._events],
    }


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
