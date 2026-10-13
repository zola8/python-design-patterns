# Level 2: Cloud & Architectural Patterns (Macro / System-Level)

These patterns deal with distributed systems.
They solve problems that don't exist in a single process: network latency, partial failures, scaling across multiple
servers, and data consistency.

Because they solve different problems, we classify Cloud patterns into these 4 main buckets:

1. Resiliency & Reliability Patterns
   The network is unreliable. How do we handle failures gracefully?
    - Circuit Breaker: Stop calling a failing service to give it time to recover (prevents cascading failures).
    - Retry: Automatically retry a failed network request with exponential backoff.
    - Bulkhead: Isolate resources (like thread pools) so if one part of the system fails, it doesn't drain resources
      from
      the rest.

2. Data Management Patterns
   How do we handle massive amounts of data across distributed databases?
    - CQRS (Command Query Responsibility Segregation): Use one database model for updating data (Writes) and a
      completely
      different, read-optimized model for reading data (Reads).
    - Sharding (Data Partitioning): Split a massive database horizontally across multiple servers.
    - Cache-Aside: The application loads data from the database into a cache (like Redis) on demand.

3. Messaging & Communication Patterns
   How do decoupled microservices talk to each other?
    - Publisher/Subscriber (Pub/Sub): Services publish events to a topic, and any number of services can subscribe to
      them (e.g., AWS SNS/SQS, Kafka).
    - Competing Consumers: Multiple instances of a service pull messages from a single queue to process them in
      parallel.
    - API Gateway: A single entry point for all clients, which routes requests to the appropriate backend microservices.

4. Deployment & Infrastructure Patterns
   How do we structure our containers and infrastructure?
    - Sidecar: Deploy a helper container alongside your main application container (e.g., a logging agent or proxy) in
      the
      same pod.
    - Ambassador: A proxy container that handles external network routing and retries for your main application.

# Level 3: Enterprise Integration Patterns (The Middle Ground)

Just for your awareness, there is a middle ground between pure code and pure cloud.
These patterns (popularized by Gregor Hohpe) deal with how distinct applications exchange messages.

- Message Broker: An intermediary that translates messages between different formats.
- Correlation Identifier: Attaching an ID to a message so you can track it across multiple different systems.
