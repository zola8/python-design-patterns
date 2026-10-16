# The Event Sourcing Pattern

The Event Sourcing Pattern is about storing state changes as a sequence of events instead of storing just the current
state.

#### What you lose:

- No history: Who changed the balance? When? Why?
- No audit trail: Can't prove compliance (SOX, GDPR, banking regulations)
- No time travel: Can't see what the balance was yesterday
- No debugging: Can't replay events to find bugs
- Data loss on bugs: If your code has a bug that corrupts state, it's gone forever

#### What you gain:

- Full audit trail: Every change is recorded
- Time travel: Query balance at any point in time
- Debugging: Replay events to reproduce bugs
- Multiple views: Build different read models from the same events (CQRS!)
- Data integrity: Events are append-only, can't be accidentally overwritten

### Event Sourcing Best Practices & Pitfalls

Events are immutable. Once written, NEVER modify or delete them. If there's a mistake, create a new corrective event (
e.g., DepositReversed). This is the entire point of the pattern.

Use past tense for event names. Deposited, Withdrew, AccountOpened — not Deposit, Withdraw, OpenAccount. Events are
facts, not commands.

Include correlation IDs. Link related events together:

```
metadata={"correlation_id": "transfer-123"}  # Links TransferOut + TransferIn
```

# Testing Event-Sourced Systems

Testing event-sourced systems is different from testing CRUD apps. You're not testing "does the database have the right
row?" — you're testing:

1. Event derivation: Do events produce the correct state?
2. Business rules: Are invalid commands rejected?
3. Immutability: Are events truly append-only?
4. Time travel: Can we reconstruct past states?
5. Audit trail: Is the event log complete and consistent?
