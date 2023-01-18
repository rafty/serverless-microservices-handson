import aws_cdk
from constructs import Construct
from aws_cdk import aws_lambda
from aws_cdk import aws_events
from aws_cdk import aws_events_targets
from aws_cdk import aws_sqs
from aws_cdk import aws_lambda_event_sources
from aws_cdk import aws_sam


class DeliveryFunctionConstructor(Construct):

    def __init__(self, scope: "Construct", id_: str, props: dict = None) -> None:
        super().__init__(scope, id_)
        self.props = props
        self.delivery_table = props['delivery_table']
        self.delivery_event_table = props['delivery_event_table']
        self.courier_table = props['courier_table']
        self.restaurant_replica_table = props['restaurant_replica_table']

        self.function = self.create_delivery_function()

    def create_delivery_function(self) -> aws_lambda.Function:

        delivery_function = aws_lambda.Function(
            self,
            'DeliveryFunction',
            function_name='delivery_service_function',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('application-food_delivery'
                                            '/delivery_service/delivery_function'),
            tracing=aws_lambda.Tracing.ACTIVE,  # for X-Ray
            layers=[self.lambda_powertools()],  # for X-Ray SDK
            environment={
                'DYNAMODB_TABLE_NAME': self.delivery_table.table_name,
                'DYNAMODB_EVENT_TABLE_NAME': self.delivery_event_table.table_name,
                'COURIER_TABLE_NAME': self.courier_table.table_name,
                'DYNAMODB_RESTAURANT_REPLICA_TABLE_NAME': self.restaurant_replica_table.table_name,
            }
        )
        self.delivery_table.table.grant_read_write_data(delivery_function)
        self.delivery_event_table.table.grant_read_write_data(delivery_function)
        self.courier_table.table.grant_read_write_data(delivery_function)
        self.restaurant_replica_table.table.grant_read_write_data(delivery_function)

        # Event Bridge - Restaurant ServiceからのEventを受け取る
        self.add_restaurant_event_bus_target(delivery_function)
        self.add_order_event_bus_target(delivery_function)
        self.add_ticket_event_bus_target(delivery_function)

        return delivery_function

    def add_restaurant_event_bus_target(self, lambda_function):
        restaurant_service_eventbus_arn = aws_cdk.Fn.import_value('RestaurantServiceEventBusARN')
        restaurant_eventbus = aws_events.EventBus.from_event_bus_arn(
            self,
            'RestaurantServiceEventBus',
            event_bus_arn=restaurant_service_eventbus_arn
        )
        restaurant_service_created_event_rule = aws_events.Rule(
            self,
            'DeliveryServiceRestaurantCreatedRule',
            rule_name='RestaurantEventsRuleForDeliveryService',  # RuleはService毎に名前を変える必要
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

    def add_order_event_bus_target(self, lambda_function):
        order_service_eventbus_arn = aws_cdk.Fn.import_value('OrderServiceEventBusARN')
        order_eventbus = aws_events.EventBus.from_event_bus_arn(
            self,
            'OrderServiceEventBus',
            event_bus_arn=order_service_eventbus_arn
        )
        order_service_created_event_rule = aws_events.Rule(
            self,
            'DeliveryServiceOrderCreatedRule',
            rule_name='OrderCreatedRuleForDeliveryService',  # RuleはService毎に名前を変える必要がある
            description='When Order microservice created the Order',
            event_bus=order_eventbus,
            event_pattern=aws_events.EventPattern(
                source=['com.order.created'],
                detail_type=['OrderCreated'],
            ),
            enabled=True,
        )

        dead_letter_queue = aws_sqs.Queue(self, 'DeliveryOrderCreatedEventDeadLetterQueue')

        order_service_created_event_rule.add_target(
                                            aws_events_targets.LambdaFunction(
                                                lambda_function,
                                                dead_letter_queue=dead_letter_queue,
                                                max_event_age=aws_cdk.Duration.hours(2),
                                                retry_attempts=2))

    def add_ticket_event_bus_target(self, lambda_function):
        kitchen_service_ticket_eventbus_arn = aws_cdk.Fn.import_value(
                                                                'KitchenServiceTicketEventBusARN')
        ticket_eventbus = aws_events.EventBus.from_event_bus_arn(
            self,
            'KitchenServiceTicketEventBus',
            event_bus_arn=kitchen_service_ticket_eventbus_arn
        )
        kitchen_service_ticket_accepted_event_rule = aws_events.Rule(
            self,
            'DeliveryServiceTicketAcceptedEventRule',
            rule_name='TicketEventsRuleForDeliveryService',  # RuleはService毎に名前を変える必要
            description='When Kitchen microservice accepted Ticket',
            event_bus=ticket_eventbus,
            event_pattern=aws_events.EventPattern(
                source=['com.ticket.accepted'],
                detail_type=['TicketAccepted'],
            ),
            enabled=True,
        )

        dead_letter_queue = aws_sqs.Queue(self, 'DeliveryTicketAcceptedEventDeadLetterQueue')

        kitchen_service_ticket_accepted_event_rule.add_target(
                                                    aws_events_targets.LambdaFunction(
                                                        lambda_function,
                                                        dead_letter_queue=dead_letter_queue,
                                                        max_event_age=aws_cdk.Duration.hours(2),
                                                        retry_attempts=2))

    def lambda_powertools(self):
        power_tools_layer = aws_sam.CfnApplication(
            scope=self,
            id='AWSLambdaPowertoolsLayer',
            location={
                'applicationId': ('arn:aws:serverlessrepo:eu-west-1:057560766410'
                                  ':applications/aws-lambda-powertools-python-layer'),
                'semanticVersion': '2.6.0'
            }
        )
        power_tools_layer_arn = power_tools_layer.get_att('Outputs.LayerVersionArn').to_string()
        power_tools_layer_version = aws_lambda.LayerVersion.from_layer_version_arn(
                scope=self,
                id='AWSLambdaPowertoolsLayerVersion',
                layer_version_arn=power_tools_layer_arn)
        return power_tools_layer_version


class DeliveryEventFunctionConstructor(Construct):

    def __init__(self, scope: "Construct", id_: str, props: dict) -> None:
        super().__init__(scope, id_)
        self.props = props
        self.dynamodb_streams_source = props['dynamodb_streams_source']

        self.eventbus = props['eventbus']
        self.eventbus_name = self.eventbus.eventbus.event_bus_name
        self.event_source = self.eventbus.event_source
        self.event_detail_type = self.eventbus.event_detail_type

        self.function = self.create_delivery_event_function()

    def create_delivery_event_function(self) -> aws_lambda.Function:

        function = aws_lambda.Function(
            self,
            'DeliveryEventFunction',
            function_name='delivery_event_function',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('application-food_delivery/delivery_service'
                                            '/delivery_domain_event_function'),
            tracing=aws_lambda.Tracing.ACTIVE,  # for X-Ray
            layers=[self.lambda_powertools()],  # for X-Ray SDK
            environment={
                'EVENT_BUS_NAME': self.eventbus_name,
                'EVENT_SOURCE': self.event_source,
                'EVENT_DETAIL_TYPE': self.event_detail_type,
            },
        )
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

    def lambda_powertools(self):
        power_tools_layer = aws_sam.CfnApplication(
            scope=self,
            id='AWSLambdaPowertoolsLayer',
            location={
                'applicationId': ('arn:aws:serverlessrepo:eu-west-1:057560766410'
                                  ':applications/aws-lambda-powertools-python-layer'),
                'semanticVersion': '2.6.0'
            }
        )
        power_tools_layer_arn = power_tools_layer.get_att('Outputs.LayerVersionArn').to_string()
        power_tools_layer_version = aws_lambda.LayerVersion.from_layer_version_arn(
                scope=self,
                id='AWSLambdaPowertoolsLayerVersion',
                layer_version_arn=power_tools_layer_arn)
        return power_tools_layer_version