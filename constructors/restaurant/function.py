from constructs import Construct
from aws_cdk import aws_lambda
from aws_cdk import aws_lambda_event_sources


class RestaurantFunctionConstructor(Construct):

    def __init__(self, scope: "Construct", id_: str, props: dict = None) -> None:
        super().__init__(scope, id_)
        self.props = props
        self.restaurant_table = props['restaurant_table']
        self.restaurant_event_table = props['restaurant_event_table']
        self.function = self.create_restaurant_function()

    def create_restaurant_function(self) -> aws_lambda.Function:

        restaurant_function = aws_lambda.Function(
            self,
            'RestaurantFunction',
            function_name='restaurant_service_function',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('application-food_delivery'
                                            '/restaurant_service/restaurant_function'),
            environment={
                'DYNAMODB_TABLE_NAME': 'RestaurantService',
                'DYNAMODB_EVENT_TABLE_NAME': 'RestaurantEvent',
            }
        )
        self.restaurant_table.table.grant_read_write_data(restaurant_function)
        self.restaurant_event_table.table.grant_read_write_data(restaurant_function)

        return restaurant_function


class RestaurantEventFunctionConstructor(Construct):

    def __init__(self, scope: "Construct", id_: str, props: dict) -> None:
        super().__init__(scope, id_)
        self.props = props
        self.eventbus = props['eventbus']
        self.eventbus_name = self.eventbus.eventbus.event_bus_name
        self.event_source = self.eventbus.event_source
        self.event_detail_type = self.eventbus.event_detail_type

        self.function = self.create_restaurant_event_function()

    def create_restaurant_event_function(self) -> aws_lambda.Function:

        function = aws_lambda.Function(
            self,
            'RestaurantEventFunction',
            function_name='restaurant_event_function',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('application-food_delivery/restaurant_service'
                                            '/restaurant_domain_event_function'),
            environment={
                'EVENT_BUS_NAME': self.eventbus_name,
                'EVENT_SOURCE': self.event_source,
                'EVENT_DETAIL_TYPE': self.event_detail_type,
            },
        )
        self.eventbus.eventbus.grant_put_events_to(function)

        function.add_event_source(
            aws_lambda_event_sources.DynamoEventSource(
                table=self.props.get('dynamodb_streams_source'),
                starting_position=aws_lambda.StartingPosition.LATEST,
                # filters=[{"event_name": aws_lambda.FilterRule.is_equal("INSERT")}]
            )
        )

        return function
