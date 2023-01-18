import aws_cdk
from constructs import Construct
from aws_cdk import aws_lambda
from aws_cdk import aws_events
from aws_cdk import aws_events_targets
from aws_cdk import aws_sqs
from aws_cdk import aws_lambda_event_sources
from aws_cdk import aws_sam


class KitchenFunctionConstructor(Construct):

    def __init__(self, scope: "Construct", id_: str, props: dict = None) -> None:
        super().__init__(scope, id_)
        self.props = props
        self.kitchen_table = props['kitchen_table']
        self.kitchen_event_table = props['kitchen_event_table']
        self.restaurant_replica_table = props['restaurant_replica_table']

        self.function = self.create_kitchen_function()

    def create_kitchen_function(self) -> aws_lambda.Function:

        kitchen_function = aws_lambda.Function(
            self,
            'KitchenServiceFunction',
            function_name='kitchen_service_function',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('application-food_delivery'
                                            '/kitchen_service/kitchen_function'),
            tracing=aws_lambda.Tracing.ACTIVE,  # for X-Ray
            layers=[self.lambda_powertools()],  # for X-Ray SDK
            environment={
                'DYNAMODB_TABLE_NAME': self.kitchen_table.table_name,
                'DYNAMODB_EVENT_TABLE_NAME': self.kitchen_event_table.table_name,
                'DYNAMODB_RESTAURANT_REPLICA_TABLE_NAME': self.restaurant_replica_table.table_name,
            }
        )
        self.kitchen_table.table.grant_read_write_data(kitchen_function)
        self.kitchen_event_table.table.grant_read_write_data(kitchen_function)
        self.restaurant_replica_table.table.grant_read_write_data(kitchen_function)

        self.add_event_bus_target(kitchen_function)

        # Cross Stack Reference for CreateOrder Saga StepFunctions state
        aws_cdk.CfnOutput(
            self,
            'KitchenServiceFunctionARN',
            value=kitchen_function.function_arn,
            description='Kitchen Service Lambda Function ARN',
            export_name='KitchenServiceFunctionARN'
        )

        return kitchen_function

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
            rule_name='RestaurantCreatedRuleForKitchenService',  # Todo: Service毎に名前を変える必要がある
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


class KitchenEventFunctionConstructor(Construct):

    def __init__(self, scope: "Construct", id_: str, props: dict) -> None:
        super().__init__(scope, id_)
        self.props = props
        self.dynamodb_streams_source = props['dynamodb_streams_source']

        self.eventbus = props['eventbus']
        self.eventbus_name = self.eventbus.eventbus.event_bus_name
        self.event_source = self.eventbus.event_source
        self.event_detail_type = self.eventbus.event_detail_type

        self.function = self.create_kitchen_event_function()

    def create_kitchen_event_function(self) -> aws_lambda.Function:

        function = aws_lambda.Function(
            self,
            'KitchenEventFunction',
            function_name='kitchen_event_function',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('application-food_delivery/kitchen_service'
                                            '/kitchen_domain_event_function'),
            tracing=aws_lambda.Tracing.ACTIVE,  # for X-Ray
            layers=[self.lambda_powertools()],  # for X-Ray SDK
            environment={
                'EVENT_BUS_NAME': self.eventbus_name,
                'EVENT_SOURCE': self.event_source,
                'EVENT_DETAIL_TYPE': self.event_detail_type,
            },
        )
        self.eventbus.eventbus.grant_put_events_to(function)

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