import aws_cdk
from aws_cdk import Stack
from constructs import Construct
from constructors.delivery import dynamodb
from constructors.delivery import function
from constructors.delivery import api_gateway
from constructors.delivery import eventbridge


class DeliveryServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------
        # Dynamo DB
        # ------------------------------------------------------
        delivery_table = dynamodb.DeliveryTableConstructor(self, 'DeliveryTableConstructor')
        delivery_event_table = dynamodb.DeliveryEventTableConstructor(self, 'DeliveryEventConstructor')
        courier_table = dynamodb.CourierTableConstructor(self, 'CourierTableConstructor')
        restaurant_replica_table = dynamodb.RestaurantReplicaTableConstructor(
                                            self, 'RestaurantReplicaTableConstructor')
        # ------------------------------------------------------
        # AWS Lambda function
        # ------------------------------------------------------
        delivery_function = function.DeliveryFunctionConstructor(
                        self,
                        'DeliveryServiceFunction',
                        props={
                            'delivery_table': delivery_table,
                            'delivery_event_table': delivery_event_table,
                            'courier_table': courier_table,
                            'restaurant_replica_table': restaurant_replica_table,
                        })

        # ------------------------------------------------------
        # REST API
        # ------------------------------------------------------
        # Todo: 複数サービスのAPIを一つのConstructorする。
        courier_api = api_gateway.CourierRestApiConstructor(
            self,
            'CourierRestApiConstructor',
            props={
                'function': delivery_function.function
            }
        )

        # ------------------------------------------------------
        #  Event Bus
        # ------------------------------------------------------
        delivery_eventbus = eventbridge.DeliveryEventBusConstructor(
            self,
            'DeliveryEventBusConstructor',
            props={},
        )
        aws_cdk.CfnOutput(
            self,
            'DeliveryServiceEventBusARN',
            value=delivery_eventbus.eventbus.event_bus_arn,
            description='Delivery Service Eventbus ARN',
            export_name='DeliveryServiceEventBusARN'
        )

        # ------------------------------------------------------
        #  AWS Lambda Function for Delivery Event Table & SAGA
        # ------------------------------------------------------
        delivery_event_function = function.DeliveryEventFunctionConstructor(
            self,
            'DeliveryEventFunctionConstructor',
            props={
                'dynamodb_streams_source': delivery_event_table.table,
                'eventbus': delivery_eventbus,
            },
        )

