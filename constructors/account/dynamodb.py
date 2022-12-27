import aws_cdk
from constructs import Construct
from aws_cdk import aws_dynamodb


class AccountTableConstructor(Construct):
    def __init__(self, scope: "Construct", id: str) -> None:
        super().__init__(scope, id)
        self.table_name = 'AccountService'
        self.partition_key = 'PK'
        self.sort_key = 'SK'

        self.table = self.create_account_table()

    def create_account_table(self) -> aws_dynamodb.Table:
        table = aws_dynamodb.Table(
            self,
            id='AccountServiceDynamodbTable',
            table_name=self.table_name,
            partition_key=aws_dynamodb.Attribute(name=self.partition_key,
                                                 type=aws_dynamodb.AttributeType.STRING),
            sort_key=aws_dynamodb.Attribute(name=self.sort_key,
                                            type=aws_dynamodb.AttributeType.STRING),
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST
        )
        return table


class AccountEventTableConstructor(Construct):
    def __init__(self, scope: "Construct", id: str) -> None:
        super().__init__(scope, id)
        self.table_name = 'AccountEvent'
        self.partition_key = 'PK'
        self.sort_key = 'SK'
        self.table = self.create_account_event_table()

    def create_account_event_table(self) -> aws_dynamodb.Table:
        table = aws_dynamodb.Table(
            self,
            id='AccountEventDynamodbTable',
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
