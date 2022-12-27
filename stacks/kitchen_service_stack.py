import aws_cdk
from aws_cdk import Stack
from constructs import Construct
from constructors.kitchen import dynamodb
from constructors.kitchen import function
from constructors.kitchen import api_gateway
from constructors.kitchen import eventbridge


class KitchenServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---------------------------------------------------------------
        # Dynamo DB
        # ---------------------------------------------------------------
        kitchen_table = dynamodb.KitchenTableConstructor(
                                            self, 'KitchenTableConstructor')
        kitchen_event_table = dynamodb.KitchenEventTableConstructor(
                                            self, 'KitchenEventConstructor')
        restaurant_replica_table = dynamodb.RestaurantReplicaTableConstructor(
                                            self, 'RestaurantReplicaTableConstructor')

        # ---------------------------------------------------------------
        # AWS Lambda function
        # ---------------------------------------------------------------
        kitchen_function = function.KitchenFunctionConstructor(
                        self,
                        'KitchenServiceFunction',
                        props={
                            'kitchen_table': kitchen_table,
                            'kitchen_event_table': kitchen_event_table,
                            'restaurant_replica_table': restaurant_replica_table,
                        })

        # ------------------------------------------------------
        # REST API
        # ------------------------------------------------------
        # Todo: 複数サービスのAPIを一つのConstructorする。
        ticket_api = api_gateway.TicketRestApiConstructor(
            self,
            'TicketRestApiConstructor',
            props={
                'function': kitchen_function.function
            }
        )

        # ------------------------------------------------------
        #  Event Bus
        # ------------------------------------------------------
        ticket_eventbus = eventbridge.TicketEventBusConstructor(
            self,
            'TicketEventBusConstructor',
            props={},
        )
        aws_cdk.CfnOutput(
            self,
            'KitchenServiceTicketEventBusARN',
            value=ticket_eventbus.eventbus.event_bus_arn,
            description='Kitchen Service Ticket Accept eventbus ARN',
            export_name='KitchenServiceTicketEventBusARN'
        )

        # ------------------------------------------------------
        #  AWS Lambda Function for Kitchen Event Table
        # ------------------------------------------------------
        kitchen_event_function = function.KitchenEventFunctionConstructor(
            self,
            'KitchenEventFunctionConstructor',
            props={
                'dynamodb_streams_source': kitchen_event_table.table,
                'eventbus': ticket_eventbus,
            },
        )

