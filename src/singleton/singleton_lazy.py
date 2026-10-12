import threading


class LazySingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # Acquire lock for thread safety
            with cls._lock:
                # Second check (lock acquired, safe to create)
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # IMPORTANT: __init__ is called EVERY time you call LazySingleton()
        # We must guard it so we don't overwrite our state on subsequent calls.
        if not hasattr(self, '_initialized'):
            self.state = "Lazily initialized"
            self._initialized = True
            print("Lazily initialized... Heavy resources loaded!")

    def print_self(self):
        print(self.state)
