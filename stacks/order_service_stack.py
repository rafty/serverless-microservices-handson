import aws_cdk
from aws_cdk import Stack
from constructs import Construct
from constructors.order import dynamodb
from constructors.order import function
from constructors.order import api_gateway
from constructors.order import stepfunctions_create_order_saga
from constructors.order import stepfunctions_cancel_order_saga
from constructors.order import stepfunctions_revise_order_saga
from constructors.order import eventbridge


class OrderServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------
        # Dynamo DB
        # ------------------------------------------------------
        order_table = dynamodb.OrderTableConstructor(self, 'OrderTableConstructor')
        order_event_table = dynamodb.OrderEventTableConstructor(self, 'OrderEventConstructor')
        restaurant_replica_table = dynamodb.RestaurantReplicaTableConstructor(
                                            self, 'RestaurantReplicaTableConstructor')

        # ------------------------------------------------------
        # AWS Lambda function
        # ------------------------------------------------------
        order_function = function.OrderFunctionConstructor(
                        self,
                        'OrderServiceFunction',
                        props={
                            'env': kwargs.get('env'),  # aws_cdk.Environment
                            'order_table': order_table,
                            'order_event_table': order_event_table,
                            'restaurant_replica_table': restaurant_replica_table,
                        })

        # ------------------------------------------------------
        # REST API
        # ------------------------------------------------------
        # Todo: 複数サービスのAPIを一つのConstructorする。
        order_api = api_gateway.OrderRestApiConstructor(
            self,
            'OrderRestApiConstructor',
            props={
                'function': order_function.function
            }
        )

        # ------------------------------------------------------
        #  StepFunctions for Saga
        # ------------------------------------------------------

        # ---
        #  Create Order Saga
        create_order_saga_stepfunction = stepfunctions_create_order_saga.CreateOrderSagaStepFunctions(
            self,
            'CreateOrderSagaConstructor',
            props={
                'order_service_function': order_function.function,
            }
        )
        # ---
        #  Cancel Order Saga
        cancel_order_saga_stepfunction = stepfunctions_cancel_order_saga.CancelOrderSagaStepFunctions(
            self,
            'CancelOrderSagaConstructor',
            props={
                'order_service_function': order_function.function,
            }
        )
        # ---
        #  Revise Order Saga
        revise_order_saga_stepfunction = stepfunctions_revise_order_saga.ReviseOrderSagaStepFunctions(
            self,
            'ReviseOrderSagaConstructor',
            props={
                'order_service_function': order_function.function,
            }
        )

        # ------------------------------------------------------
        #  Event Bus
        # ------------------------------------------------------
        order_eventbus = eventbridge.OrderEventBusConstructor(
            self,
            'OrderEventBusConstructor',
            props={},
        )
        aws_cdk.CfnOutput(
            self,
            'OrderServiceEventBusARN',
            value=order_eventbus.eventbus.event_bus_arn,
            description='Order Service create order eventbus ARN',
            export_name='OrderServiceEventBusARN'
        )

        # ------------------------------------------------------
        #  AWS Lambda Function for Order Event Table & SAGA
        # ------------------------------------------------------
        order_event_function = function.OrderEventFunctionConstructor(
            self,
            'OrderEventFunctionConstructor',
            props={
                'dynamodb_streams_source': order_event_table.table,
                'eventbus': order_eventbus,
                'state_machine_for_create_order_saga': create_order_saga_stepfunction.state_machine,
                'state_machine_for_cancel_order_saga': cancel_order_saga_stepfunction.state_machine,
                'state_machine_for_revise_order_saga': revise_order_saga_stepfunction.state_machine,
            },
        )

