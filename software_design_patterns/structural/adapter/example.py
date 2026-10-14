from abc import ABC
from abc import abstractmethod


# ==========================================
# 1. YOUR TARGET INTERFACE (What your app expects)
# ==========================================

class Notifier(ABC):
    """The interface your entire app is built around."""

    @abstractmethod
    def send(self, to: str, message: str) -> bool:
        pass


# ==========================================
# 2. THE ADAPTEES (External SDKs you can't change)
# ==========================================

class TwilioSDK:
    """Simulates Twilio's actual SDK — weird interface."""

    def __init__(self, account_sid, auth_token):
        self.account_sid = account_sid

    def messages_create(self, body: str, from_number: str, to_number: str):
        print(f"[Twilio] Sending SMS from {from_number} to {to_number}: {body}")
        return {"sid": "SM123", "status": "sent"}


class SendGridSDK:
    """Simulates SendGrid's actual SDK — totally different interface."""

    def __init__(self, api_key):
        self.api_key = api_key

    def mail_send(self, from_email: str, to_emails: list, subject: str, content: str):
        print(f"[SendGrid] Email from {from_email} to {to_emails}: {content}")
        return {"status": "delivered", "message_id": "abc123"}


# ==========================================
# 3. THE ADAPTERS (The translators)
# ==========================================

class TwilioSMSAdapter(Notifier):
    """Adapts Twilio's SDK to our Notifier interface."""

    def __init__(self, twilio_client: TwilioSDK, sender_number: str):
        self._twilio = twilio_client
        self._sender = sender_number  # Hide this detail from our app!

    def send(self, to: str, message: str) -> bool:
        # Translate our simple interface -> Twilio's complex one
        result = self._twilio.messages_create(
            body=message,
            from_number=self._sender,
            to_number=to
        )
        return result["status"] == "sent"


class SendGridEmailAdapter(Notifier):
    """Adapts SendGrid's SDK to our Notifier interface."""

    def __init__(self, sendgrid_client: SendGridSDK, from_email: str):
        self._sendgrid = sendgrid_client
        self._from_email = from_email  # Hide this detail from our app!

    def send(self, to: str, message: str) -> bool:
        # Translate our simple interface -> SendGrid's complex one
        result = self._sendgrid.mail_send(
            from_email=self._from_email,
            to_emails=[to],
            subject="Notification",  # We provide a default — our app doesn't care
            content=message
        )
        return result["status"] == "delivered"


# ==========================================
# 4. YOUR BUSINESS LOGIC (Clean and stable)
# ==========================================

def notify_user(notifier: Notifier, user_email_or_phone: str, message: str):
    """This function will NEVER need to change, no matter what channels you add."""
    success = notifier.send(user_email_or_phone, message)
    if success:
        print(f"Notification delivered to {user_email_or_phone}")
    else:
        print(f"Failed to notify {user_email_or_phone}")


# ==========================================
# 5. USAGE
# ==========================================

if __name__ == "__main__":
    # Setup external SDKs (probably in your app's startup/config)
    twilio = TwilioSDK(account_sid="AC123", auth_token="secret")
    sendgrid = SendGridSDK(api_key="SG.xyz")

    # Wrap them in adapters
    sms_notifier = TwilioSMSAdapter(twilio, sender_number="+12345")
    email_notifier = SendGridEmailAdapter(sendgrid, from_email="noreply@email.com")

    # Business logic uses the unified interface
    notify_user(sms_notifier, "+456789", "Your order has shipped!")
    notify_user(email_notifier, "alice@example.com", "Welcome to our platform!")
