# CQRS (Command Query Responsibility Segregation)

CQRS is an architectural pattern that separates read operations (queries) from write operations (commands) into
completely different models.
The same data might be represented differently depending on whether you're reading it or writing it.

---

#### Scenario: A blog with posts and comments.

_The Problem._

You have two tables:

- posts (id, title, content, author_id)
- comments (id, post_id, text, author)

Writing a comment: You insert into the comments table. Simple.

Reading a post with all comments: You need to JOIN posts + comments. If you do this on every read, it's slow.
The CQRS insight: Optimize writes and reads separately.

**Write model**: Normalized, transactional, optimized for data integrity.

**Read model**: Denormalized, fast, optimized for specific queries.

---

Write side (BlogWriteModel): Adds a comment to the normalized comments list. Doesn't care about reads.

Read side (BlogReadModel): Builds a denormalized view by joining post + comments on the fly. Doesn't care about writes.

Same fake DB, but different models optimized for different operations.
