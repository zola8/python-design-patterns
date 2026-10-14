from functools import wraps


# use @wraps: When writing functional decorators, always use from functools import wraps.
# If you don't, the decorated function loses its original __name__ and __doc__, which breaks debugging, logging, and tools like FastAPI/Swagger.


# The Functional Decorators
def log_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[LOG] Calling {func.__name__}...")
        result = func(*args, **kwargs)
        print(f"[LOG] {func.__name__} finished.")
        return result

    return wrapper


def encrypt_payload(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        encrypted = f"ENCRYPTED({message})"
        return func(encrypted, *args, **kwargs)

    return wrapper


# The Core Function
# Execution: A wraps (B wraps (func))
@log_execution
@encrypt_payload
def send_sms(message: str):
    print(f"[Basic SMS] Sending: {message}")


if __name__ == '__main__':
    send_sms("Hello World")
