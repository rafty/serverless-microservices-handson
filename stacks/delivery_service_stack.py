from aws_cdk import Stack
from constructs import Construct
from constructors.delivery import dynamodb
from constructors.delivery import function
from constructors.delivery import api_gateway


class DeliveryServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------
        # Dynamo DB
        # ------------------------------------------------------
        delivery_table = dynamodb.DeliveryTableConstructor(self, 'DeliveryTableConstructor')
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
