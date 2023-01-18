import aws_cdk
from constructs import Construct
from aws_cdk import aws_dynamodb


class OrderHistoryTableConstructor(Construct):
    def __init__(self, scope: "Construct", id: str) -> None:
        super().__init__(scope, id)
        self.table_name = 'OrderHistoryService'
        self.partition_key = 'PK'
        self.sort_key = 'SK'

        self.table = self.create_order_history_table()

    def create_order_history_table(self) -> aws_dynamodb.Table:
        table = aws_dynamodb.Table(
            self,
            id='OrderHistoryServiceDynamodbTable',
            table_name=self.table_name,
            partition_key=aws_dynamodb.Attribute(name=self.partition_key,
                                                 type=aws_dynamodb.AttributeType.STRING),
            sort_key=aws_dynamodb.Attribute(name=self.sort_key,
                                            type=aws_dynamodb.AttributeType.STRING),
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # DynamoDB GSI for sparce index
        table.add_global_secondary_index(index_name='OrderHistoryByConsumerIdAndCreationTime',
                                         partition_key=aws_dynamodb.Attribute(
                                                        name='consumer_id',
                                                        type=aws_dynamodb.AttributeType.NUMBER),
                                         sort_key=aws_dynamodb.Attribute(
                                                        name='creation_date',
                                                        type=aws_dynamodb.AttributeType.STRING),
                                         projection_type=aws_dynamodb.ProjectionType.ALL,
                                         # read_capacity=1,  PAY_PER_REQUESTなので指定できない
                                         # write_capacity=1  PAY_PER_REQUESTなので指定できない
                                         )

        return table
