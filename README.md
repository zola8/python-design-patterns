# python-design-patterns

#### Install dependencies

```shell
pip install -r requirements.txt
```

#### Organization of the patterns

```
DESIGN PATTERNS
│
├── 1. CODE-LEVEL (Inside one app/process) -> "Gang of Four"
│   ├── Creational (Singleton, Factory, Builder)
│   ├── Structural (Decorator, Adapter, Facade)
│   └── Behavioral (Strategy, Observer, State)
│
├── 2. INTEGRATION-LEVEL (Between distinct apps) -> "Enterprise Integration"
│   ├── Message Channels (Pub/Sub, Point-to-Point)
│   └── Message Routing (Content-Based Router)
│
└── 3. SYSTEM-LEVEL (Distributed systems/Cloud) -> "Cloud Native"
    ├── Resiliency (Circuit Breaker, Retry, Bulkhead)
    ├── Data (CQRS, Sharding, Cache-Aside)
    ├── Communication (API Gateway, Competing Consumers)
    └── Deployment (Sidecar, Ambassador)
```
