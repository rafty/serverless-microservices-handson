import aws_cdk
from constructs import Construct
from aws_cdk import aws_lambda
from aws_cdk import aws_events
from aws_cdk import aws_events_targets
from aws_cdk import aws_sqs
from aws_cdk import aws_lambda_event_sources
from aws_cdk import aws_sam


class ConsumerFunctionConstructor(Construct):

    def __init__(self, scope: "Construct", id_: str, props: dict = None) -> None:
        super().__init__(scope, id_)
        self.props = props
        self.consumer_table = props['consumer_table']
        self.consumer_event_table = props['consumer_event_table']

        self.function = self.create_consumer_function()

    def create_consumer_function(self) -> aws_lambda.Function:

        consumer_function = aws_lambda.Function(
            self,
            'ConsumerFunction',
            function_name='consumer_service_function',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('application-food_delivery'
                                            '/consumer_service/consumer_function'),
            tracing=aws_lambda.Tracing.ACTIVE,  # for X-Ray
            layers=[self.lambda_powertools()],  # for X-Ray SDK
            environment={
                'DYNAMODB_TABLE_NAME': self.consumer_table.table_name,
                'DYNAMODB_EVENT_TABLE_NAME': self.consumer_event_table.table_name,
            }
        )
        self.consumer_table.table.grant_read_write_data(consumer_function)
        self.consumer_event_table.table.grant_read_write_data(consumer_function)

        # Cross Stack Reference for CreateOrder Saga StepFunctions state
        aws_cdk.CfnOutput(
            self,
            'ConsumerServiceFunctionARN',
            value=consumer_function.function_arn,
            description='Consumer Service Lambda Function ARN',
            export_name='ConsumerServiceFunctionARN'
        )

        return consumer_function

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


class ConsumerEventFunctionConstructor(Construct):

    def __init__(self, scope: "Construct", id_: str, props: dict) -> None:
        super().__init__(scope, id_)
        self.props = props
        self.dynamodb_streams_source = props['dynamodb_streams_source']

        self.function = self.create_consumer_event_function()

    def create_consumer_event_function(self) -> aws_lambda.Function:

        function = aws_lambda.Function(
            self,
            'ConsumerEventFunction',
            function_name='consumer_event_function',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('application-food_delivery/consumer_service'
                                            '/consumer_domain_event_function'),
            tracing=aws_lambda.Tracing.ACTIVE,  # for X-Ray
            layers=[self.lambda_powertools()],  # for X-Ray SDK
            environment={},
        )

        # DynamoDB Streams Source
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
