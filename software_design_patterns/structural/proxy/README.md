# The Proxy Pattern

"I Don't Want Everyone to Access This."

Common scenarios:

- **Expensive object**: Loading a 500MB image from disk. You don't want to load it until someone actually calls
  .display().
- **Sensitive object**: A database of user passwords. You want to check permissions before allowing access.
- **Remote object**: A service running on another server. You want a local stand-in that handles network calls.
- **Shared object**: A database connection. You want to cache results or pool connections.
