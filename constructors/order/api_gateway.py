from constructs import Construct
from aws_cdk import aws_apigateway


class OrderRestApiConstructor(Construct):

    def __init__(self, scope: "Construct", id: str, props: dict) -> None:
        super().__init__(scope, id)

        self.api: aws_apigateway.LambdaRestApi = None
        self.props = props
        self.order_api()

    def order_api(self) -> None:
        self.api = aws_apigateway.LambdaRestApi(
            self,
            'OrderServiceRestApi',
            handler=self.props['function'],
            proxy=False,
            deploy_options=aws_apigateway.StageOptions(
                data_trace_enabled=True,
                logging_level=aws_apigateway.MethodLoggingLevel.INFO,
                metrics_enabled=True,
                tracing_enabled=True,
            )
        )
        self.rest_resource_and_method()

    def rest_resource_and_method(self) -> None:
        """
        Resource and Method

            /orders
                - POST          : create order

            /orders/{order_id}
                - GET           : fetch single order

            /orders/{order_id}/cancel
                - POST          : cancel order
        """
        orders = self.api.root.add_resource('orders')
        orders.add_method('POST')

        single_order = orders.add_resource('{order_id}')
        single_order.add_method('GET')

        cancel_single_order = single_order.add_resource('cancel')
        cancel_single_order.add_method('POST')

        revise_single_order = single_order.add_resource('revise')
        revise_single_order.add_method('POST')
