# The Bulkhead Pattern

The Bulkhead Pattern is about isolating resources so that a failure in one part of your system doesn't sink
the whole ship.

In software: if your app calls 3 external services (Payment, Email, Analytics), give each its own pool of resources
(threads, connections, semaphores). If the Email service hangs and exhausts its pool,
the Payment service keeps working normally.

In async Python, the simplest bulkhead is a semaphore — a counter that limits concurrent access.

### Separate Pools (Bulkheads)

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Email Pool (3)  │  │ Payment Pool(5) │  │ Analytics (2)   │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ 3 workers stuck │  │ 5 workers free  │  │ 2 workers free  │
│ Email fails     │  │ Payments OK     │  │ Analytics OK    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```
