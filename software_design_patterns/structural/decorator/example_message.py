from abc import ABC
from abc import abstractmethod


# 1. The Component Interface
class MessageSender(ABC):
    @abstractmethod
    def send(self, message: str): pass


# 2. The Concrete Component (The core object)
class BasicSender(MessageSender):
    def send(self, message: str):
        print(f"[Basic] Sending: {message}")


# 3. The Base Decorator (Follows the Component interface, but holds a reference to it)
class MessageDecorator(MessageSender):
    def __init__(self, sender: MessageSender):
        self._sender = sender  # The wrapped object

    def send(self, message: str):
        self._sender.send(message)


# 4. Concrete Decorators (Adding specific behaviors)
class LoggingDecorator(MessageDecorator):
    def send(self, message: str):
        print(f"[LOG] Preparing to send message...")
        super().send(message)  # Delegates to the wrapped object
        print(f"[LOG] Message sent successfully.")


class EncryptionDecorator(MessageDecorator):
    def send(self, message: str):
        # Modify the data before passing it down the chain
        encrypted_msg = f"ENCRYPTED({message})"
        super().send(encrypted_msg)


if __name__ == '__main__':
    # Scenario A: Just basic sending
    sender = BasicSender()
    sender.send("Hello")

    print("-" * 30)

    # Scenario B: Basic + Logging
    logged_sender = LoggingDecorator(BasicSender())
    logged_sender.send("Hello")

    print("-" * 30)

    # Scenario C: Basic + Encryption + Logging
    # Notice the order! The outermost decorator runs first.
    secure_sender = LoggingDecorator(EncryptionDecorator(BasicSender()))
    secure_sender.send("Secret Password")
