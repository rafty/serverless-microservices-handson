from constructs import Construct
from aws_cdk import aws_apigateway


class CourierRestApiConstructor(Construct):

    def __init__(self, scope: "Construct", id: str, props: dict) -> None:
        super().__init__(scope, id)

        self.api: aws_apigateway.LambdaRestApi = None
        self.props = props
        self.courier_api()

    def courier_api(self) -> None:
        self.api = aws_apigateway.LambdaRestApi(
            self,
            'DeliveryServiceCourierRestApi',
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
            /couriers/{courier_id}/availability
                - POST          : courier available

            /couriers/{courier_id}/pickedup
                - POST          : courier delivery pickedup

            /couriers/{courier_id}/delivered
                - POST          : courier delivery delivered

        """
        couriers = self.api.root.add_resource('couriers')
        single_courier = couriers.add_resource('{courier_id}')

        cancel_single_courier = single_courier.add_resource('availability')
        cancel_single_courier.add_method('POST')

        cancel_single_courier = single_courier.add_resource('pickedup')
        cancel_single_courier.add_method('POST')

        cancel_single_courier = single_courier.add_resource('delivered')
        cancel_single_courier.add_method('POST')
