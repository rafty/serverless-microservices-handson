import aws_cdk
from aws_cdk import Stack
from constructs import Construct
from constructors.order_history import dynamodb
from constructors.order_history import function
from constructors.order_history import api_gateway


class OrderHistoryServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------
        # Dynamo DB
        # ------------------------------------------------------
        order_history_table = dynamodb.OrderHistoryTableConstructor(
                                                self, 'OrderHistoryServiceOrderTableConstructor')

        # ------------------------------------------------------
        # AWS Lambda function
        # ------------------------------------------------------
        order_history_function = function.OrderHistoryFunctionConstructor(
                        self,
                        'OrderHistoryServiceFunction',
                        props={
                            'order_history_table': order_history_table,
                        })

        # ------------------------------------------------------
        # REST API
        # ------------------------------------------------------
        # 重要: API Compositionは対応せず、CQRSの対応をする。

        order_api = api_gateway.OrderHistoryRestApiConstructor(
            self,
            'OrderHistoryRestApiConstructor',
            props={
                'function': order_history_function.function
            }
        )

