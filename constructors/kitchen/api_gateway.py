from constructs import Construct
from aws_cdk import aws_apigateway


class TicketRestApiConstructor(Construct):

    def __init__(self, scope: "Construct", id: str, props: dict) -> None:
        super().__init__(scope, id)

        self.api: aws_apigateway.LambdaRestApi = None
        self.props = props
        self.ticket_api()

    def ticket_api(self) -> None:
        self.api = aws_apigateway.LambdaRestApi(
            self,
            'KitchenServiceTicketRestApi',
            handler=self.props['function'],
            proxy=False
        )
        self.rest_resource_and_method()

    def rest_resource_and_method(self) -> None:
        """
        Ticket and Method
            /ticket/{ticket_id}/accept
                - POST          : ticket accept
        """
        tickets = self.api.root.add_resource('tickets')
        single_ticket = tickets.add_resource('{ticket_id}')
        accept_single_ticket = single_ticket.add_resource('accept')
        accept_single_ticket.add_method('POST')
