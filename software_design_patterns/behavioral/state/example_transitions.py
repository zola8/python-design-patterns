from transitions import Machine


class Order:
    def __init__(self):
        self.machine = Machine(
            model=self,
            states=['pending', 'paid', 'shipped'],
            initial='pending',
            transitions=[
                {'trigger': 'pay', 'source': 'pending', 'dest': 'paid'},
                {'trigger': 'ship', 'source': 'paid', 'dest': 'shipped'},
            ]
        )


# methods are auto-generated!

if __name__ == '__main__':
    order = Order()
    print(order.state)  # 'pending'

    order.pay()
    print(order.state)  # 'paid'

    order.ship()
    print(order.state)  # 'shipped'

    # Invalid transition returns False
    result = order.pay()  # False — can't pay from 'shipped'
    print(f"Pay result: {result}, state: {order.state}")
