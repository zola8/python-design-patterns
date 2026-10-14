### Without Observer

```python
class OrderService:
    def __init__(self, email_service, inventory_service, warehouse_service, analytics_service, notification_service):
        # TIGHT COUPLING — OrderService knows about EVERYTHING
        self.email = email_service
        self.inventory = inventory_service
        self.warehouse = warehouse_service
        self.analytics = analytics_service
        self.notification = notification_service
    
    def place_order(self, order: Order):
        # Save order to database
        db.save(order)
        
        # Now notify everyone — 30 lines of orchestration
        self.email.send_confirmation(order.user_email, order.id)
        self.inventory.decrease_stock(order.items)
        self.warehouse.prepare_shipment(order)
        self.analytics.track_order_placed(order)
        self.notification.send_push(order.user_id, "Your order is confirmed!")
```

Every time you add a new action (e.g., "send SMS"), you have to modify OrderService.
