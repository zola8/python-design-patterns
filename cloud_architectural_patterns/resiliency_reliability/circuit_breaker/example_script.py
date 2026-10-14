import time

from resiliency_reliability.circuit_breaker.core_sync import CircuitBreaker
from resiliency_reliability.circuit_breaker.core_sync import CircuitOpenError
from resiliency_reliability.circuit_breaker.core_sync import circuit_protected


# ==========================================
# 3. THE MOCK EXTERNAL SERVICE
# ==========================================

class MockAPI:
    """Simulates an external API that is down for the first 3 calls, then recovers."""

    def __init__(self):
        self.call_count = 0

    def fetch_data(self):
        self.call_count += 1
        print(f"  [Mock API] Actually called network (Call #{self.call_count})")

        # Simulate network failures
        if self.call_count <= 3:
            raise ConnectionError("Network unreachable!")

        return {"status": "success", "data": "Hello from API!"}


# ==========================================
# 4. THE MAIN ENTRY POINT
# ==========================================

# Setup our mock API and the Circuit Breaker
api = MockAPI()

# Threshold: 3 failures. Timeout: 2 seconds.
breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=2.0,
    expected_exceptions=(ConnectionError,),
    name="MockAPI"
)


@circuit_protected(breaker)
def get_data():
    return api.fetch_data()


if __name__ == "__main__":
    # --- SIMULATION START ---

    print("=== PHASE 1: Triggering Failures (CLOSED -> OPEN) ===")
    for i in range(1, 5):
        try:
            print(f"Attempt {i}: ", end="")
            get_data()
        except ConnectionError as e:
            print(f"Failed ({e}) | Breaker State: {breaker.state.value}")
        except CircuitOpenError as e:
            print(f"BLOCKED! ({e}) | Breaker State: {breaker.state.value}")

    print("\n=== PHASE 2: Waiting for Recovery Timeout ===")
    print(f"Current State: {breaker.state.value}")
    print("Sleeping for 2 seconds to let the timeout expire...")
    time.sleep(2.1)
    print(f"State after sleep: {breaker.state.value}")

    print("\n=== PHASE 3: Half-Open Probe (Testing recovery) ===")
    try:
        print("Attempt 5: ", end="")
        result = get_data()
        print(f"Success! {result} | Breaker State: {breaker.state.value}")
    except Exception as e:
        print(f"Failed ({e}) | Breaker State: {breaker.state.value}")

    print("\n=== PHASE 4: Back to Normal (CLOSED) ===")
    try:
        print("Attempt 6: ", end="")
        result = get_data()
        print(f"Success! {result} | Breaker State: {breaker.state.value}")
    except Exception as e:
        print(f"Failed ({e}) | Breaker State: {breaker.state.value}")
