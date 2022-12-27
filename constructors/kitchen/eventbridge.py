from constructs import Construct
from aws_cdk import aws_events


class TicketEventBusConstructor(Construct):
    def __init__(self, scope: "Construct", id: str, props: dict) -> None:
        super().__init__(scope, id)

        self.props = props
        self.name = 'KitchenTicketServiceChannel'
        self.eventbus = None
        self.event_source = 'com.ticket.accepted'
        self.event_detail_type = 'TicketAccepted'

        self.create_ticket_eventbus()

    def create_ticket_eventbus(self) -> aws_events.EventBus:

        self.eventbus = aws_events.EventBus(
            self,
            'KitchenTicketEventBus',
            event_bus_name=self.name,
        )
