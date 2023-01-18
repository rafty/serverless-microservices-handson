import aws_cdk
from constructs import Construct
from aws_cdk import aws_lambda
from aws_cdk import aws_events
from aws_cdk import aws_events_targets
from aws_cdk import aws_sqs
from aws_cdk import aws_lambda_event_sources
from aws_cdk import aws_sam


class OrderHistoryFunctionConstructor(Construct):

    def __init__(self, scope: "Construct", id_: str, props: dict = None) -> None:
        super().__init__(scope, id_)
        self.props = props
        self.order_history_table = props['order_history_table']
        self.function = self.create_order_history_function()

    def create_order_history_function(self) -> aws_lambda.Function:

        order_history_function = aws_lambda.Function(
            self,
            'OrderHistoryFunction',
            function_name='order_history_service_function',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('application-food_delivery'
                                            '/order_history_service/order_history_function'),
            tracing=aws_lambda.Tracing.ACTIVE,  # for X-Ray
            layers=[self.lambda_powertools()],  # for X-Ray SDK
            environment={
                'DYNAMODB_TABLE_NAME': self.order_history_table.table_name,
            }
        )
        # function grant
        self.order_history_table.table.grant_read_write_data(order_history_function)

        # add EventBus
        self.add_order_event_bus_target(order_history_function)
        self.add_delivery_event_bus_target(order_history_function)

        return order_history_function

    def add_order_event_bus_target(self, lambda_function):
        order_service_eventbus_arn = aws_cdk.Fn.import_value('OrderServiceEventBusARN')
        order_eventbus = aws_events.EventBus.from_event_bus_arn(
            self,
            'OrderServiceEventBus',
            event_bus_arn=order_service_eventbus_arn
        )
        order_history_service_order_event_rule = aws_events.Rule(
            self,
            'OrderHistoryServiceOrderEventRule',
            rule_name='OrderHistoryServiceOrderEventRule',
            description='Order Service Events',
            event_bus=order_eventbus,
            event_pattern=aws_events.EventPattern(
                source=['com.order.created'],
                detail_type=['OrderCreated'],
            ),
            enabled=True,
        )

        dead_letter_queue = aws_sqs.Queue(self, 'OrderHistoryOrderCreatedEventDeadLetterQueue')

        order_history_service_order_event_rule.add_target(
                                            aws_events_targets.LambdaFunction(
                                                lambda_function,
                                                dead_letter_queue=dead_letter_queue,
                                                max_event_age=aws_cdk.Duration.hours(2),
                                                retry_attempts=2))

    # Todo: ここから 2023.01.16
    #  DeliveryServiceからEventを受け取る
    def add_delivery_event_bus_target(self, lambda_function):

        delivery_service_eventbus_arn = aws_cdk.Fn.import_value('DeliveryServiceEventBusARN')
        delivery_eventbus = aws_events.EventBus.from_event_bus_arn(
            self,
            'DeliveryServiceEventBus',
            event_bus_arn=delivery_service_eventbus_arn
        )
        order_history_service_delivery_event_rule = aws_events.Rule(
            self,
            'OrderHistoryServiceDeliveryEventRule',
            rule_name='OrderHistoryServiceDeliveryEventRule',
            description='Delivery Service Events',
            event_bus=delivery_eventbus,
            event_pattern=aws_events.EventPattern(
                source=['com.delivery.created'],
                detail_type=['DeliveryCreated'],
            ),
            enabled=True,
        )

        dead_letter_queue = aws_sqs.Queue(self, 'OrderHistoryDeliveryEventDeadLetterQueue')

        order_history_service_delivery_event_rule.add_target(
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
