import aws_cdk
from aws_cdk import Stack
from constructs import Construct
from constructors.restaurant import dynamodb
from constructors.restaurant import function
from constructors.restaurant import api_gateway
from constructors.restaurant import eventbridge


class RestaurantServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------
        # Dynamo DB
        # ------------------------------------------------------
        restaurant_table = dynamodb.RestaurantTableConstructor(self, 'RestaurantTableConstructor')
        restaurant_event_table = dynamodb.RestaurantEventTableConstructor(
                                                self, 'RestaurantEventTableConstructor')

        # ------------------------------------------------------
        # AWS Lambda function
        # ------------------------------------------------------
        restaurant_function = function.RestaurantFunctionConstructor(
            self,
            'RestaurantFunctionConstructor',
            props={
                # 'table': restaurant_table.table,
                'restaurant_table': restaurant_table,
                'restaurant_event_table': restaurant_event_table,
            },
        )

        # ------------------------------------------------------
        # REST API
        # ------------------------------------------------------
        # Todo: 複数サービスのAPIを一つのConstructorする。
        restaurant_api = api_gateway.RestaurantRestApiConstructor(
            self,
            'RestaurantRestApiConstructor',
            props={
                'function': restaurant_function.function
            }
        )

        # ------------------------------------------------------
        #  Event Bus
        # ------------------------------------------------------
        restaurant_eventbus = eventbridge.RestaurantEventBusConstructor(
            self,
            'RestaurantEventBusConstructor',
            props={},
        )

        # ------------------------------------------------------
        # AWS Lambda function - Event function
        # ------------------------------------------------------
        restaurant_event_function = function.RestaurantEventFunctionConstructor(
            self,
            'RestaurantEventFunctionConstructor',
            props={
                'dynamodb_streams_source': restaurant_event_table.table,
                'eventbus': restaurant_eventbus,
            },
        )

        # ------------------------------------------------------
        # CfnOutput
        # ------------------------------------------------------
        aws_cdk.CfnOutput(
            self,
            'RestaurantServiceEventBusARN',
            value=restaurant_eventbus.eventbus.event_bus_arn,
            description='Restaurant Service create restaurant and menu eventbus ARN',
            export_name='RestaurantServiceEventBusARN'
        )
