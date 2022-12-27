from constructs import Construct
from aws_cdk import aws_apigateway


class RestaurantRestApiConstructor(Construct):

    def __init__(self, scope: "Construct", id: str, props: dict) -> None:
        super().__init__(scope, id)

        self.api: aws_apigateway.LambdaRestApi = None
        self.props = props
        self.restaurant_api()

    def restaurant_api(self) -> None:
        self.api = aws_apigateway.LambdaRestApi(
            self,
            'RestaurantServiceRestApi',
            handler=self.props['function'],
            proxy=False
        )
        self.rest_resource_and_method()

    def rest_resource_and_method(self) -> None:
        """
        Resource and Method

            /restaurants
                - POST          : create restaurant

            /restaurants/{restaurant_id}
                - GET           : fetch single restaurant

        """
        restaurant = self.api.root.add_resource('restaurants')
        restaurant.add_method('POST')

        single_restaurant = restaurant.add_resource('{restaurant_id}')
        single_restaurant.add_method('GET')
