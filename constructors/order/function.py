import aws_cdk
from constructs import Construct
from aws_cdk import aws_lambda
from aws_cdk import aws_events
from aws_cdk import aws_events_targets
from aws_cdk import aws_sqs
from aws_cdk import aws_lambda_event_sources


class OrderFunctionConstructor(Construct):

    def __init__(self, scope: "Construct", id_: str, props: dict = None) -> None:
        super().__init__(scope, id_)
        self.props = props
        self.order_table = props['order_table']
        self.order_event_table = props['order_event_table']
        self.restaurant_replica_table = props['restaurant_replica_table']
        self.function = self.create_order_function()

    def create_order_function(self) -> aws_lambda.Function:

        order_function = aws_lambda.Function(
            self,
            'OrderFunction',
            function_name='order_service_function',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('application-food_delivery'
                                            '/order_service/order_function'),
            environment={
                'DYNAMODB_TABLE_NAME': self.order_table.table_name,
                'DYNAMODB_EVENT_TABLE_NAME': self.order_event_table.table_name,
                'DYNAMODB_RESTAURANT_REPLICA_TABLE_NAME': self.restaurant_replica_table.table_name,
            }
        )
        self.order_table.table.grant_read_write_data(order_function)
        self.order_event_table.table.grant_read_write_data(order_function)
        self.restaurant_replica_table.table.grant_read_write_data(order_function)

        self.add_event_bus_target(order_function)

        return order_function

    def add_event_bus_target(self, lambda_function):
        restaurant_service_eventbus_arn = aws_cdk.Fn.import_value('RestaurantServiceEventBusARN')
        restaurant_eventbus = aws_events.EventBus.from_event_bus_arn(
            self,
            'RestaurantServiceEventBus',
            event_bus_arn=restaurant_service_eventbus_arn
        )
        restaurant_service_created_event_rule = aws_events.Rule(
            self,
            'RestaurantServiceRestaurantCreatedRule',
            rule_name='RestaurantServiceRestaurantCreatedRule',
            description='When Restaurant microservice created the restaurant and menu',
            event_bus=restaurant_eventbus,
            event_pattern=aws_events.EventPattern(
                source=['com.restaurant.created'],
                detail_type=['RestaurantCreated'],
            ),
            enabled=True,
        )

        dead_letter_queue = aws_sqs.Queue(self, 'RestaurantCreatedEventDeadLetterQueue')

        restaurant_service_created_event_rule.add_target(
                                            aws_events_targets.LambdaFunction(
                                                lambda_function,
                                                dead_letter_queue=dead_letter_queue,
                                                max_event_age=aws_cdk.Duration.hours(2),
                                                retry_attempts=2))


class OrderEventFunctionConstructor(Construct):

    def __init__(self, scope: "Construct", id_: str, props: dict) -> None:
        super().__init__(scope, id_)
        self.props = props
        self.dynamodb_streams_source = props['dynamodb_streams_source']
        self.state_machine_for_create_order_saga = props['state_machine_for_create_order_saga']
        self.state_machine_for_cancel_order_saga = props['state_machine_for_cancel_order_saga']
        self.state_machine_for_revise_order_saga = props['state_machine_for_revise_order_saga']

        self.eventbus = props['eventbus']
        self.eventbus_name = self.eventbus.eventbus.event_bus_name
        self.event_source = self.eventbus.event_source
        self.event_detail_type = self.eventbus.event_detail_type

        self.function = self.create_order_event_function()

    def create_order_event_function(self) -> aws_lambda.Function:

        function = aws_lambda.Function(
            self,
            'OrderEventFunction',
            function_name='order_event_function',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('application-food_delivery/order_service'
                                            '/order_domain_event_function'),
            environment={
                'STATEMACHINE_ARN_FOR_CREATE_ORDER_SAGA': self.state_machine_for_create_order_saga.state_machine_arn,
                'STATEMACHINE_ARN_FOR_CANCEL_ORDER_SAGA': self.state_machine_for_cancel_order_saga.state_machine_arn,
                'STATEMACHINE_ARN_FOR_REVISE_ORDER_SAGA': self.state_machine_for_revise_order_saga.state_machine_arn,
                'EVENT_BUS_NAME': self.eventbus_name,
                'EVENT_SOURCE': self.event_source,
                'EVENT_DETAIL_TYPE': self.event_detail_type,
            },
        )
        self.state_machine_for_create_order_saga.grant_start_execution(function)
        self.state_machine_for_cancel_order_saga.grant_start_execution(function)
        self.state_machine_for_revise_order_saga.grant_start_execution(function)
        self.eventbus.eventbus.grant_put_events_to(function)

        # DynamoDB Streams
        function.add_event_source(
            aws_lambda_event_sources.DynamoEventSource(
                table=self.dynamodb_streams_source,
                starting_position=aws_lambda.StartingPosition.LATEST,
                # filters=[{"event_name": aws_lambda.FilterRule.is_equal("INSERT")}]
            )
        )

        return function
