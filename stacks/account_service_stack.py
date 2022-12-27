from aws_cdk import Stack
from constructs import Construct
from constructors.account import dynamodb
from constructors.account import function
from constructors.account import api_gateway


class AccountServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------
        # Dynamo DB
        # ------------------------------------------------------
        account_table = dynamodb.AccountTableConstructor(self, 'AccountTableConstructor')
        account_event_table = dynamodb.AccountEventTableConstructor(
                                                            self, 'AccountEventConstructor')

        # ------------------------------------------------------
        # AWS Lambda function
        # ------------------------------------------------------
        account_function = function.AccountFunctionConstructor(
                        self,
                        'AccountServiceFunction',
                        props={
                            'account_table': account_table,
                            'account_event_table': account_event_table,
                        })

        # ------------------------------------------------------
        # ApiGateway
        # ------------------------------------------------------
        # Todo: 複数サービスのAPIを一つのConstructorする。
        restaurant_api = api_gateway.AccountRestApiConstructor(
            self,
            'AccountRestApiConstructor',
            props={
                'function': account_function.function
            }
        )

        # Todo: 後で実装
        # # ------------------------------------------------------
        # #  AWS Lambda Function for Account Event Table
        # # ------------------------------------------------------
        # account_event_function = function.AccountEventFunctionConstructor(
        #     self,
        #     'AccountEventFunctionConstructor',
        #     props={
        #         'dynamodb_streams_source': account_event_table.table,
        #     },
        # )
