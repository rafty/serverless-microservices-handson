from constructs import Construct
from aws_cdk import aws_events


class DeliveryEventBusConstructor(Construct):
    def __init__(self, scope: "Construct", id: str, props: dict) -> None:
        super().__init__(scope, id)

        self.props = props
        self.name = 'DeliveryServiceChannel'
        self.eventbus = None
        self.event_source = 'com.delivery.created'
        self.event_detail_type = 'DeliveryCreated'

        self.create_delivery_eventbus()

    def create_delivery_eventbus(self) -> aws_events.EventBus:

        self.eventbus = aws_events.EventBus(
            self,
            'DeliveryEventBus',
            event_bus_name=self.name,
        )
