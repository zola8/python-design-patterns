"""Unit tests for the Account aggregate — pure logic, no HTTP."""
from datetime import datetime
from datetime import timedelta

from cloud_architectural_patterns.data_management_patterns.event_sourcing.example_bank_account import Account
from cloud_architectural_patterns.data_management_patterns.event_sourcing.example_bank_account import Event


def make_event(event_type: str, amount: float, hours_ago: int = 0) -> Event:
    """Helper to create test events."""
    return Event(
        event_id=f"evt-{event_type}-{amount}",
        account_id="alice",
        event_type=event_type,
        amount=amount,
        timestamp=datetime.now() - timedelta(hours=hours_ago),
    )


class TestAccountEventReplay:
    """Test that events correctly derive account state."""

    def test_empty_account(self):
        """An account with no events shouldn't exist."""
        account = Account("alice", [])
        assert account.balance == 0.0
        assert account.created_at is None

    def test_open_account_with_initial_deposit(self):
        events = [make_event("AccountOpened", 100)]
        account = Account("alice", events)
        assert account.balance == 100.0
        assert account.created_at is not None

    def test_deposit_increases_balance(self):
        events = [
            make_event("AccountOpened", 0),
            make_event("Deposited", 50),
            make_event("Deposited", 30),
        ]
        account = Account("alice", events)
        assert account.balance == 80.0
        assert account.transaction_count == 2

    def test_withdraw_decreases_balance(self):
        events = [
            make_event("AccountOpened", 100),
            make_event("Withdrew", 30),
        ]
        account = Account("alice", events)
        assert account.balance == 70.0

    def test_transfer_events(self):
        events = [
            make_event("AccountOpened", 100),
            make_event("TransferOut", 40),
        ]
        account = Account("alice", events)
        assert account.balance == 60.0

    def test_complex_sequence(self):
        """Realistic sequence of events."""
        events = [
            make_event("AccountOpened", 0),
            make_event("Deposited", 1000),  # Salary
            make_event("Withdrew", 200),  # Rent
            make_event("Deposited", 50),  # Refund
            make_event("TransferOut", 100),  # Send to friend
            make_event("Withdrew", 50),  # Groceries
        ]
        account = Account("alice", events)
        assert account.balance == 700.0  # 1000 - 200 + 50 - 100 - 50
        assert account.transaction_count == 5


class TestTimeTravel:
    """Test reconstructing state at a point in time."""

    def test_balance_at_past_time(self):
        """Can we see what the balance was yesterday?"""
        now = datetime.now()

        # Use make_event helper for consistency
        events = [
            make_event("AccountOpened", 0, hours_ago=72),  # 3 days ago
            make_event("Deposited", 100, hours_ago=48),  # 2 days ago
            make_event("Deposited", 50, hours_ago=24),  # 1 day ago
            make_event("Withdrew", 30, hours_ago=0),  # Now
        ]

        # Define a "past" moment: just after the second deposit (2 days ago)
        # We want to exclude the 3rd deposit (1 day ago) and the withdrawal (now)
        past_cutoff = now - timedelta(hours=25)

        # Filter events manually to simulate the "before" query
        past_events = [e for e in events if e.timestamp < past_cutoff]

        account = Account("alice", past_events)

        # Should only include: Opened (0) + Deposited (100)
        assert account.balance == 100.0
        assert account.transaction_count == 1  # Only the deposit counts as a transaction

        # Current state: all events
        account_now = Account("alice", events)
        assert account_now.balance == 120.0  # 0 + 100 + 50 - 30
        assert account_now.transaction_count == 3
