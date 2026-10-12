from abc import ABC
from abc import abstractmethod


# 1. Define the interface
class PaymentProcessor(ABC):
    @abstractmethod
    def pay(self, amount: float): pass


class CreditCardProcessor(PaymentProcessor):
    def pay(self, amount: float): print(f"Paid ${amount} via Credit Card")


class PayPalProcessor(PaymentProcessor):
    def pay(self, amount: float): print(f"Paid ${amount} via PayPal")


# 2. The Simple Factory
def create_payment_processor(method: str) -> PaymentProcessor:
    match method.lower():
        case "credit_card":
            return CreditCardProcessor()
        case "paypal":
            return PayPalProcessor()
        case _:
            raise ValueError(f"Unknown payment method: {method}")


if __name__ == '__main__':
    processor = create_payment_processor("paypal")
    processor.pay(50.00)
