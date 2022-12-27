from constructs import Construct
from aws_cdk import aws_events


class OrderEventBusConstructor(Construct):
    def __init__(self, scope: "Construct", id: str, props: dict) -> None:
        super().__init__(scope, id)

        self.props = props
        self.name = 'OrderServiceChannel'
        self.eventbus = None
        self.event_source = 'com.order.created'
        self.event_detail_type = 'OrderCreated'

        self.create_order_eventbus()

    def create_order_eventbus(self) -> aws_events.EventBus:

        self.eventbus = aws_events.EventBus(
            self,
            'OrderEventBus',
            event_bus_name=self.name,
        )
