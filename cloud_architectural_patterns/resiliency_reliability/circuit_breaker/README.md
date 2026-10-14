# The Circuit Breaker Pattern

This is one of the most important Cloud/Resiliency patterns, and honestly one of the most practical things you can add
to any Python service that talks to the outside world.

### The Problem It Solves

Imagine your Python service calls a third-party Payment API. That API goes down.
Without a circuit breaker, here's what happens:

- Request comes in → your service calls Payment API → waits 30 seconds for a timeout → fails.
- 100 more requests come in → 100 threads/async tasks are now blocked waiting on a dead service.
- Your thread pool is exhausted. Your health check times out. Your load balancer marks you unhealthy.
- Your service is now dead too — even though the part of your system that was actually broken was someone else's API.

This is called a cascading failure. The Circuit Breaker stops it.

### The Three States

```
        ┌─────────────────────────────────────────┐
        │                                         │
        ▼                                         │
   ┌─────────┐   N failures   ┌─────────┐  timeout ┌───────────┐
   │ CLOSED  ├───────────────►│  OPEN   ├─────────►│ HALF-OPEN │
   └─────────┘                └─────────┘          └───────────┘
        ▲                            ▲                   │
        │                            │                   │
        └──────── success ───────────┴───── failure ────┘
```

- CLOSED ✅
  Normal. Requests flow through. Failures are counted.
- OPEN ❌
  Broken. Requests are rejected instantly (no network call). Waits for cooldown.
- HALF-OPEN 🧪
  Cooldown expired. Let one trial request through to test.

