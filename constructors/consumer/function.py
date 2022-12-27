import aws_cdk
from constructs import Construct
from aws_cdk import aws_lambda
from aws_cdk import aws_events
from aws_cdk import aws_events_targets
from aws_cdk import aws_sqs
from aws_cdk import aws_lambda_event_sources


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
            environment={
            },
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
