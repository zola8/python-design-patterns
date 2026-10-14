import threading
import time
from enum import Enum
from functools import wraps


# ==========================================
# 1. THE CIRCUIT BREAKER IMPLEMENTATION
# ==========================================

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitOpenError(Exception):
    """Raised when the circuit is OPEN and the call is rejected immediately."""


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exceptions: tuple = (ConnectionError, TimeoutError),
        name: str = "default",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        self.name = name

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at: float | None = None
        self._probe_in_flight = False
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #
    def call(self, func, *args, **kwargs):
        """Execute func through the circuit."""
        self._check_allows_request()
        try:
            result = func(*args, **kwargs)
        except self.expected_exceptions as exc:
            self._on_failure(exc)
            raise
        else:
            self._on_success()
            return result

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._maybe_transition_to_half_open()
            return self._state

    # ------------------------------------------------------------------ #
    #  State machine
    # ------------------------------------------------------------------ #
    def _check_allows_request(self):
        with self._lock:
            self._maybe_transition_to_half_open()

            if self._state is CircuitState.OPEN:
                raise CircuitOpenError(
                    f"Circuit '{self.name}' is OPEN — failing fast."
                )

            if self._state is CircuitState.HALF_OPEN:
                # CRITICAL: only ONE probe is allowed through at a time.
                # Otherwise a recovering service gets stampeded by 100 requests.
                if self._probe_in_flight:
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' is HALF_OPEN — probe already in flight."
                    )
                self._probe_in_flight = True

    def _maybe_transition_to_half_open(self):
        """Called with the lock held."""
        if self._state is CircuitState.OPEN:
            elapsed = time.monotonic() - (self._opened_at or 0)
            if elapsed >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._probe_in_flight = False

    def _on_success(self):
        with self._lock:
            self._failure_count = 0
            self._probe_in_flight = False
            self._state = CircuitState.CLOSED
            self._opened_at = None
            # Log/emit metric: "circuit recovered"

    def _on_failure(self, exc):
        with self._lock:
            self._probe_in_flight = False
            self._failure_count += 1

            # In HALF_OPEN, a single failure trips it immediately.
            if self._state is CircuitState.HALF_OPEN or \
                self._failure_count >= self.failure_threshold:
                self._trip()

    def _trip(self):
        self._state = CircuitState.OPEN
        self._opened_at = time.monotonic()
        self._failure_count = 0
        # Log/emit metric: "circuit OPEN — service unhealthy"


# ==========================================
# 2. THE DECORATOR
# ==========================================

def circuit_protected(breaker: CircuitBreaker):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator
