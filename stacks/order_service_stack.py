from aws_cdk import Stack
from constructs import Construct
from constructors.order_service import dynamodb


class OrderServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

