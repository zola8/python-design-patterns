# Layered Architecture

A well-structured FastAPI app has 4 layers, and each layer uses specific patterns:

```
┌─────────────────────────────────────────────────┐
│  HTTP Request                                   │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  1. PRESENTATION LAYER (API)                    │  ← Routers, Schemas, Deps
│     Patterns: DTO, Dependency Injection         │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  2. DOMAIN LAYER (Business Logic)               │  ← Services, Entities, Events
│     Patterns: Facade, Observer, State, Strategy │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  3. INFRASTRUCTURE LAYER (External Concerns)    │  ← DB, Email, Cache, 3rd-party
│     Patterns: Repository, Circuit Breaker,      │
│               Adapter, Proxy                    │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  4. DATA / EXTERNAL SYSTEMS                     │
│     PostgreSQL, Redis, Stripe, SendGrid, etc.   │
└─────────────────────────────────────────────────┘
```

Key rule: Dependencies point downward only. The Domain layer never imports from Infrastructure — it defines
interfaces (ABCs), and Infrastructure implements them. This is the Dependency Inversion Principle.

### The Folder Structure

```
my_project/
├── main.py                    # FastAPI app + lifespan
├── config.py                  # Settings (env vars)
│
├── api/                       # PRESENTATION LAYER
│   ├── deps.py                # Dependency injection functions
│   └── routes/
│       └── orders.py          # HTTP endpoints
│
├── domain/                    # DOMAIN LAYER (pure Python, no FastAPI imports)
│   ├── entities.py            # Business objects (Order, OrderItem)
│   ├── services.py            # Business logic (Facade)
│   ├── events.py              # Event bus (Observer)
│   └── ports.py               # Interfaces (Repository, EmailSender)
│
├── infrastructure/            # INFRASTRUCTURE LAYER
│   ├── repositories.py        # DB implementations (Repository)
│   ├── email.py               # Email providers (Strategy + Circuit Breaker)
│   └── database.py            # DB connection
│
└── schemas/                   # DTOs (Pydantic models)
    └── orders.py
```
