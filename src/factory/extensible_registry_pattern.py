class NotificationFactory:
    # Class-level dictionary to hold our creators
    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, channel: str, handler_class: type):
        """Allows registering new handlers without modifying the factory."""
        cls._registry[channel] = handler_class

    @classmethod
    def create(cls, channel: str):
        if channel not in cls._registry:
            raise ValueError(f"Unknown channel: {channel}")
        # Instantiate and return
        return cls._registry[channel]()


class EmailNotifier: pass


class SMSNotifier: pass


if __name__ == '__main__':
    # Register them (can be done in different files/modules!)
    NotificationFactory.register("email", EmailNotifier)
    NotificationFactory.register("sms", SMSNotifier)

    notifier = NotificationFactory.create("email")
