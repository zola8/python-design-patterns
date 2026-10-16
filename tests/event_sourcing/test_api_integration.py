"""Integration tests for the API endpoints."""
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
async def test_open_account(client: AsyncClient):
    """Opening an account creates an AccountOpened event."""
    response = await client.post("/accounts", json={
        "account_id": "alice",
        "initial_deposit": 100,
    })

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "created"
    assert data["event"]["event_type"] == "AccountOpened"
    assert data["event"]["amount"] == 100


@pytest.mark.asyncio
async def test_duplicate_account_rejected(client: AsyncClient):
    """Can't open the same account twice."""
    await client.post("/accounts", json={"account_id": "alice"})
    response = await client.post("/accounts", json={"account_id": "alice"})

    assert response.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_deposit(client: AsyncClient):
    """Depositing money creates a Deposited event."""
    await client.post("/accounts", json={"account_id": "alice"})

    response = await client.post("/accounts/alice/deposit", json={
        "amount": 50,
        "description": "Salary",
    })

    assert response.status_code == 200
    assert response.json()["new_balance"] == 50.0


@pytest.mark.asyncio
async def test_withdraw_insufficient_funds(client: AsyncClient):
    """Can't withdraw more than the balance."""
    await client.post("/accounts", json={"account_id": "alice", "initial_deposit": 100})

    response = await client.post("/accounts/alice/withdraw", json={"amount": 200})

    assert response.status_code == 400
    assert "Insufficient funds" in response.json()["detail"]


@pytest.mark.asyncio
async def test_negative_amount_rejected(client: AsyncClient):
    """Negative amounts are rejected."""
    await client.post("/accounts", json={"account_id": "alice"})

    response = await client.post("/accounts/alice/deposit", json={"amount": -50})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_transfer_between_accounts(client: AsyncClient):
    """Transfers create TWO events atomically."""
    await client.post("/accounts", json={"account_id": "alice", "initial_deposit": 100})
    await client.post("/accounts", json={"account_id": "bob", "initial_deposit": 50})

    response = await client.post("/transfers", json={
        "from_account": "alice",
        "to_account": "bob",
        "amount": 30,
    })

    assert response.status_code == 200
    data = response.json()
    assert data["from_balance"] == 70.0  # 100 - 30
    assert data["to_balance"] == 80.0  # 50 + 30
    assert len(data["events"]) == 2  # TransferOut + TransferIn


@pytest.mark.asyncio
async def test_transfer_insufficient_funds(client: AsyncClient):
    """Can't transfer more than the balance."""
    await client.post("/accounts", json={"account_id": "alice", "initial_deposit": 10})
    await client.post("/accounts", json={"account_id": "bob"})

    response = await client.post("/transfers", json={
        "from_account": "alice",
        "to_account": "bob",
        "amount": 100,
    })

    assert response.status_code == 400
