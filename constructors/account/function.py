import aws_cdk
from constructs import Construct
from aws_cdk import aws_lambda
from aws_cdk import aws_events
from aws_cdk import aws_events_targets
from aws_cdk import aws_sqs
from aws_cdk import aws_lambda_event_sources


class AccountFunctionConstructor(Construct):

    def __init__(self, scope: "Construct", id_: str, props: dict = None) -> None:
        super().__init__(scope, id_)
        self.props = props
        self.account_table = props['account_table']
        self.account_event_table = props['account_event_table']

        self.function = self.create_account_function()

    def create_account_function(self) -> aws_lambda.Function:

        account_function = aws_lambda.Function(
            self,
            'AccountFunction',
            function_name='account_service_function',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('application-food_delivery'
                                            '/account_service/account_function'),
            environment={
                'DYNAMODB_TABLE_NAME': self.account_table.table_name,
                'DYNAMODB_EVENT_TABLE_NAME': self.account_event_table.table_name,
            }
        )
        self.account_table.table.grant_read_write_data(account_function)
        self.account_event_table.table.grant_read_write_data(account_function)

        # Cross Stack Reference for CreateOrder Saga StepFunctions state
        aws_cdk.CfnOutput(
            self,
            'AccountServiceFunctionARN',
            value=account_function.function_arn,
            description='Account Service Lambda Function ARN',
            export_name='AccountServiceFunctionARN'
        )

        return account_function

# Todo: 後で実装
# class AccountEventFunctionConstructor(Construct):
#
#     def __init__(self, scope: "Construct", id_: str, props: dict) -> None:
#         super().__init__(scope, id_)
#         self.props = props
#         self.dynamodb_streams_source = props['dynamodb_streams_source']
#
#         self.function = self.create_account_event_function()
#
#     def create_account_event_function(self) -> aws_lambda.Function:
#
#         function = aws_lambda.Function(
#             self,
#             'AccountEventFunction',
#             function_name='account_event_function',
#             runtime=aws_lambda.Runtime.PYTHON_3_9,
#             handler='lambda_function.lambda_handler',
#             code=aws_lambda.Code.from_asset('application-food_delivery/account_service'
#                                             '/account_domain_event_function'),
#             environment={
#             },
#         )
#
#         # DynamoDB Streams Source
#         function.add_event_source(
#             aws_lambda_event_sources.DynamoEventSource(
#                 table=self.dynamodb_streams_source,
#                 starting_position=aws_lambda.StartingPosition.LATEST,
#                 # filters=[{"event_name": aws_lambda.FilterRule.is_equal("INSERT")}]
#             )
#         )
#
#         return function
