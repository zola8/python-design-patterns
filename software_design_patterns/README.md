# Level 1: Software Design Patterns (Micro / Code-Level)

These are the classic Gang of Four (GoF) patterns.
They deal with classes, objects, and code inside a single application or process.

- Creational: How objects are created. (Singleton, Factory, Builder)
- Structural: How objects are composed to form larger structures. (Adapter, Decorator, Facade)
- Behavioral: How objects communicate and assign responsibilities. (Strategy, Observer, Command)

### Structural patterns

Structural patterns are about how objects are composed to form larger, more complex structures. They help you
realize relationships between entities.

The **Adapter Pattern** is all about making incompatible interfaces work together.

The **Proxy Pattern** is about controlling access to an object.
A proxy stands between the client and the real object, acting as a gatekeeper, placeholder, or intermediary.
Think of it like a credit card: it's not the actual money in your bank account, but it controls access to it.
The merchant doesn't need to know your bank details — the card (proxy) handles the transaction,
checks your balance, and only then touches the real money.

### Behavioral patterns

These are all about how objects communicate and assign responsibilities.
While Creational patterns handle object birth and Structural patterns handle composition,
Behavioral patterns handle algorithms, workflows, and interactions.

The **Strategy Pattern** is about defining a family of algorithms, encapsulating each one, and making them
interchangeable.
The client chooses which algorithm to use at runtime without changing the code that uses it.

The **Observer Pattern** is about defining a one-to-many dependency between objects
so that when one object changes state, all its dependents are notified automatically.

The **Command Pattern** is about encapsulating a request as an object, allowing you to parameterize clients
with different requests, queue or log requests, and support undoable operations.

Think of it like a restaurant order: the waiter doesn't cook the food — they take your order (a command object),
write it down, and pass it to the kitchen. The order can be queued, modified, cancelled, or even replayed later.
