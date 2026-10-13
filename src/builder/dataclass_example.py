from dataclasses import dataclass


@dataclass
class User:
    username: str
    email: str | None = None
    age: int | None = None
    tier: str = "free"


if __name__ == '__main__':
    # Usage is incredibly clean without needing a Builder class

    user = User(username="alice", email="alice@test.com", age=28)
    print(user)
