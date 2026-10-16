"""
Tests for event-sourcing-specific properties:
- Immutability
- Audit trail completeness
- Time travel
- Event ordering
"""
import time
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport
from httpx import AsyncClient

from cloud_architectural_patterns.data_management_patterns.event_sourcing.example_bank_account import app
from cloud_architectural_patterns.data_management_patterns.event_sourcing.example_bank_account import event_store


# ==========================================
# LOCAL FIXTURES (Specific to this test file)
# ==========================================

@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def _reset_event_store():
    """
    Reset event store before/after each test.
    """
    event_store._events.clear()
    yield
    event_store._events.clear()


# ==========================================
# TESTS
# ==========================================


@pytest.mark.asyncio
async def test_events_are_immutable(client: AsyncClient):
    """
    Core property: Events are NEVER modified after creation.

    This is the entire point of event sourcing.
    """
    # Create some events
    await client.post("/accounts", json={"account_id": "alice", "initial_deposit": 100})
    await client.post("/accounts/alice/deposit", json={"amount": 50})

    # Capture the events
    events_before = [e.model_copy() for e in event_store._events]

    # Do more operations
    await client.post("/accounts/alice/withdraw", json={"amount": 20})

    # Original events should be EXACTLY the same
    for before, after in zip(events_before, event_store._events[:len(events_before)]):
        assert before.event_id == after.event_id
        assert before.amount == after.amount
        assert before.timestamp == after.timestamp
        assert before.event_type == after.event_type


@pytest.mark.asyncio
async def test_audit_trail_completeness(client: AsyncClient):
    """
    Every state-changing operation produces exactly one event.

    The audit trail must be complete — no missing events.
    """
    await client.post("/accounts", json={"account_id": "alice"})
    await client.post("/accounts/alice/deposit", json={"amount": 100})
    await client.post("/accounts/alice/deposit", json={"amount": 50})
    await client.post("/accounts/alice/withdraw", json={"amount": 30})

    # Verify: exactly 4 events in the store
    events = event_store.get_events("alice")
    assert len(events) == 4

    # Verify: event types match operations
    event_types = [e.event_type for e in events]
    assert event_types == [
        "AccountOpened",
        "Deposited",
        "Deposited",
        "Withdrew",
    ]


@pytest.mark.asyncio
async def test_failed_commands_dont_produce_events(client: AsyncClient):
    """
    If a command fails validation, NO event is created.

    The audit trail only contains successful operations.
    """
    await client.post("/accounts", json={"account_id": "alice", "initial_deposit": 100})

    # Try to withdraw more than balance (should fail)
    response = await client.post("/accounts/alice/withdraw", json={"amount": 200})
    assert response.status_code == 400

    # Try negative amount (should fail)
    response = await client.post("/accounts/alice/deposit", json={"amount": -50})
    assert response.status_code == 400

    # Verify: only the initial AccountOpened event exists
    events = event_store.get_events("alice")
    assert len(events) == 1
    assert events[0].event_type == "AccountOpened"


@pytest.mark.asyncio
async def test_time_travel_via_api(client: AsyncClient):
    """
    TIME TRAVEL: Query balance at a past point in time.

    This is impossible in CRUD — unique to event sourcing.
    """
    # Create account
    await client.post("/accounts", json={"account_id": "alice", "initial_deposit": 100})
    time.sleep(0.1)  # Small delay to ensure different timestamps

    # Capture timestamp BEFORE deposit
    past_timestamp = datetime.now().isoformat()
    time.sleep(0.1)

    # Make a deposit
    await client.post("/accounts/alice/deposit", json={"amount": 50})

    # Current balance: 150
    response = await client.get("/accounts/alice")
    assert response.json()["balance"] == 150.0

    # Balance at past time: 100 (before the deposit)
    response = await client.get(f"/accounts/alice/balance-at?before={past_timestamp}")
    assert response.status_code == 200
    assert response.json()["balance"] == 100.0


@pytest.mark.asyncio
async def test_global_event_log(client: AsyncClient):
    """
    The global event log contains events from ALL accounts.

    This is the "single source of truth" for the entire system.
    """
    await client.post("/accounts", json={"account_id": "alice", "initial_deposit": 100})
    await client.post("/accounts", json={"account_id": "bob", "initial_deposit": 50})
    await client.post("/accounts/alice/deposit", json={"amount": 25})

    response = await client.get("/events")
    data = response.json()

    assert data["total_events"] == 3

    # Events should be in chronological order
    timestamps = [e["timestamp"] for e in data["events"]]
    assert timestamps == sorted(timestamps)

    # Events should include both accounts
    account_ids = {e["account_id"] for e in data["events"]}
    assert account_ids == {"alice", "bob"}


@pytest.mark.asyncio
async def test_event_ids_are_unique(client: AsyncClient):
    """Every event must have a unique ID (for idempotency and debugging)."""
    await client.post("/accounts", json={"account_id": "alice"})
    await client.post("/accounts/alice/deposit", json={"amount": 10})
    await client.post("/accounts/alice/deposit", json={"amount": 20})

    event_ids = [e.event_id for e in event_store._events]
    assert len(event_ids) == len(set(event_ids))  # All unique


@pytest.mark.asyncio
async def test_transfer_creates_correlated_events(client: AsyncClient):
    """
    A transfer creates two events that are linked.

    In a real system, you'd use correlation_id to link them.
    """
    await client.post("/accounts", json={"account_id": "alice", "initial_deposit": 100})
    await client.post("/accounts", json={"account_id": "bob"})

    response = await client.post("/transfers", json={
        "from_account": "alice",
        "to_account": "bob",
        "amount": 30,
    })

    events = response.json()["events"]
    assert len(events) == 2

    # One event per account
    assert events[0]["account_id"] == "alice"
    assert events[0]["event_type"] == "TransferOut"
    assert events[1]["account_id"] == "bob"
    assert events[1]["event_type"] == "TransferIn"

    # Same timestamp (atomic)
    assert events[0]["timestamp"] == events[1]["timestamp"]

    # Metadata links them
    assert events[0]["metadata"]["to"] == "bob"
    assert events[1]["metadata"]["from"] == "alice"
