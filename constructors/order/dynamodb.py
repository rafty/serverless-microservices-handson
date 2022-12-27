import aws_cdk
from constructs import Construct
from aws_cdk import aws_dynamodb


class OrderTableConstructor(Construct):
    def __init__(self, scope: "Construct", id: str) -> None:
        super().__init__(scope, id)
        self.table_name = 'OrderService'
        self.partition_key = 'PK'
        self.sort_key = 'SK'

        self.table = self.create_order_table()

    def create_order_table(self) -> aws_dynamodb.Table:
        table = aws_dynamodb.Table(
            self,
            id='OrderServiceDynamodbTable',
            table_name=self.table_name,
            partition_key=aws_dynamodb.Attribute(name=self.partition_key,
                                                 type=aws_dynamodb.AttributeType.STRING),
            sort_key=aws_dynamodb.Attribute(name=self.sort_key,
                                            type=aws_dynamodb.AttributeType.STRING),
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST
        )
        return table


class OrderEventTableConstructor(Construct):
    def __init__(self, scope: "Construct", id: str) -> None:
        super().__init__(scope, id)
        self.table_name = 'OrderEvent'
        self.partition_key = 'PK'
        self.sort_key = 'SK'
        self.table = self.create_order_table()

    def create_order_table(self) -> aws_dynamodb.Table:
        table = aws_dynamodb.Table(
            self,
            id='OrderEventDynamodbTable',
            table_name=self.table_name,
            partition_key=aws_dynamodb.Attribute(name=self.partition_key,
                                                 type=aws_dynamodb.AttributeType.STRING),
            sort_key=aws_dynamodb.Attribute(name=self.sort_key,
                                            type=aws_dynamodb.AttributeType.STRING),
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            stream=aws_dynamodb.StreamViewType.NEW_IMAGE,  # domain event を EventBridgeに流す
        )
        return table


class RestaurantReplicaTableConstructor(Construct):
    def __init__(self, scope: "Construct", id: str) -> None:
        super().__init__(scope, id)
        self.table_name = 'Order-RestaurantReplica'
        self.partition_key = 'PK'
        self.sort_key = 'SK'
        self.table = self.create_order_table()

    def create_order_table(self) -> aws_dynamodb.Table:
        table = aws_dynamodb.Table(
            self,
            id='Order_RestaurantReplicaDynamodbTable',
            table_name=self.table_name,
            partition_key=aws_dynamodb.Attribute(name=self.partition_key,
                                                 type=aws_dynamodb.AttributeType.STRING),
            sort_key=aws_dynamodb.Attribute(name=self.sort_key,
                                            type=aws_dynamodb.AttributeType.STRING),
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST
        )
        return table
