# The Strangler Fig Pattern

The Strangler Fig Pattern is about gradually migrating a legacy system to a modern architecture by building new features
as separate services and slowly routing traffic away from the old system — until the old system "dies" (like a strangler
fig tree that grows around a host tree and eventually kills it).

The alternative is a "Big Bang" rewrite: You stop the business for 18 months, rewrite everything, and hope it works.
This almost always fails.

Strangler Fig is the safe way: You keep the business running while you migrate piece by piece.
