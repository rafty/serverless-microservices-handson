import aws_cdk
from constructs import Construct
from aws_cdk import aws_dynamodb


class ConsumerTableConstructor(Construct):
    def __init__(self, scope: "Construct", id: str) -> None:
        super().__init__(scope, id)
        self.table_name = 'ConsumerService'
        self.partition_key = 'PK'
        self.sort_key = 'SK'

        self.table = self.create_consumer_table()

    def create_consumer_table(self) -> aws_dynamodb.Table:
        table = aws_dynamodb.Table(
            self,
            id='ConsumerServiceDynamodbTable',
            table_name=self.table_name,
            partition_key=aws_dynamodb.Attribute(name=self.partition_key,
                                                 type=aws_dynamodb.AttributeType.STRING),
            sort_key=aws_dynamodb.Attribute(name=self.sort_key,
                                            type=aws_dynamodb.AttributeType.STRING),
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST
        )
        return table


class ConsumerEventTableConstructor(Construct):
    def __init__(self, scope: "Construct", id: str) -> None:
        super().__init__(scope, id)
        self.table_name = 'ConsumerEvent'
        self.partition_key = 'PK'
        self.sort_key = 'SK'
        self.table = self.create_consumer_table()

    def create_consumer_table(self) -> aws_dynamodb.Table:
        table = aws_dynamodb.Table(
            self,
            id='ConsumerEventDynamodbTable',
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
