from constructs import Construct
from aws_cdk import aws_events


class RestaurantEventBusConstructor(Construct):
    def __init__(self, scope: "Construct", id: str, props: dict) -> None:
        super().__init__(scope, id)

        self.props = props
        self.name = 'RestaurantServiceChannel'
        self.eventbus = None
        self.event_source = 'com.restaurant.created'
        self.event_detail_type = 'RestaurantCreated'

        self.create_restaurant_eventbus()

    def create_restaurant_eventbus(self) -> aws_events.EventBus:

        self.eventbus = aws_events.EventBus(
            self,
            'BasketEventBus',
            event_bus_name=self.name,
        )
