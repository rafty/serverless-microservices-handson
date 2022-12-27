from aws_cdk import Stack
from constructs import Construct
from constructors.consumer import dynamodb
from constructors.consumer import function
from constructors.consumer import api_gateway


class ConsumerServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------
        # Dynamo DB
        # ------------------------------------------------------
        consumer_table = dynamodb.ConsumerTableConstructor(self, 'ConsumerTableConstructor')
        consumer_event_table = dynamodb.ConsumerEventTableConstructor(self, 'ConsumerEventConstructor')

        # ------------------------------------------------------
        # AWS Lambda function
        # ------------------------------------------------------
        consumer_function = function.ConsumerFunctionConstructor(
                        self,
                        'ConsumerServiceFunction',
                        props={
                            'consumer_table': consumer_table,
                            'consumer_event_table': consumer_event_table,
                        })

        # ------------------------------------------------------
        # ApiGateway
        # ------------------------------------------------------
        # Todo: 複数サービスのAPIを一つのConstructorする。
        restaurant_api = api_gateway.ConsumerRestApiConstructor(
            self,
            'ConsumerRestApiConstructor',
            props={
                'function': consumer_function.function
            }
        )

        # ------------------------------------------------------
        #  AWS Lambda Function for Consumer Event Table
        # ------------------------------------------------------
        consumer_event_function = function.ConsumerEventFunctionConstructor(
            self,
            'ConsumerEventFunctionConstructor',
            props={
                'dynamodb_streams_source': consumer_event_table.table,
            },
        )
