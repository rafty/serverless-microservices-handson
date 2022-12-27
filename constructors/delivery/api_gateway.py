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
            proxy=False
        )
        self.rest_resource_and_method()

    def rest_resource_and_method(self) -> None:
        """
        Resource and Method
            /couriers/{courier_id}/availability
                - POST          : courier available
        """
        couriers = self.api.root.add_resource('couriers')
        # couriers.add_method('POST')

        single_courier = couriers.add_resource('{courier_id}')
        # single_courier.add_method('GET')

        cancel_single_courier = single_courier.add_resource('availability')
        cancel_single_courier.add_method('POST')

