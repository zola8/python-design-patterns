import asyncio
import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitOpenError(Exception):
    pass


class AsyncCircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=30.0, expected_exceptions=(Exception,)):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at = None
        self._probe_in_flight = False
        # CRITICAL: Use asyncio.Lock for FastAPI, NOT threading.Lock
        self._lock = asyncio.Lock()

    async def call(self, func, *args, **kwargs):
        async with self._lock:
            self._check_state_transition()

            if self._state == CircuitState.OPEN:
                raise CircuitOpenError("Service is currently unavailable.")

            if self._state == CircuitState.HALF_OPEN and self._probe_in_flight:
                raise CircuitOpenError("Recovery probe already in flight.")

            if self._state == CircuitState.HALF_OPEN:
                self._probe_in_flight = True

        try:
            result = await func(*args, **kwargs)
        except self.expected_exceptions as exc:
            await self._record_failure()
            raise

        await self._record_success()
        return result

    def _check_state_transition(self):
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._opened_at >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._probe_in_flight = False

    async def _record_success(self):
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._probe_in_flight = False

    async def _record_failure(self):
        async with self._lock:
            self._probe_in_flight = False
            self._failure_count += 1
            if self._state == CircuitState.HALF_OPEN or self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                self._failure_count = 0
