import aws_cdk
from constructs import Construct
from aws_cdk import aws_dynamodb


class DeliveryTableConstructor(Construct):
    def __init__(self, scope: "Construct", id: str) -> None:
        super().__init__(scope, id)
        self.table_name = 'DeliveryService'
        self.partition_key = 'PK'
        self.sort_key = 'SK'

        self.table = self.create_delivery_table()

    def create_delivery_table(self) -> aws_dynamodb.Table:
        table = aws_dynamodb.Table(
            self,
            id='DeliveryServiceDynamodbTable',
            table_name=self.table_name,
            partition_key=aws_dynamodb.Attribute(name=self.partition_key,
                                                 type=aws_dynamodb.AttributeType.STRING),
            sort_key=aws_dynamodb.Attribute(name=self.sort_key,
                                            type=aws_dynamodb.AttributeType.STRING),
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST
        )
        return table


class DeliveryEventTableConstructor(Construct):
    def __init__(self, scope: "Construct", id: str) -> None:
        super().__init__(scope, id)
        self.table_name = 'DeliveryEvent'
        self.partition_key = 'PK'
        self.sort_key = 'SK'
        self.table = self.create_delivery_event_table()

    def create_delivery_event_table(self) -> aws_dynamodb.Table:
        table = aws_dynamodb.Table(
            self,
            id='DeliveryEventDynamodbTable',
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


class CourierTableConstructor(Construct):
    def __init__(self, scope: "Construct", id: str) -> None:
        super().__init__(scope, id)
        self.table_name = 'Delivery-Courier'
        self.partition_key = 'PK'
        self.sort_key = 'SK'

        self.table = self.create_courier_table()

    def create_courier_table(self) -> aws_dynamodb.Table:
        table = aws_dynamodb.Table(
            self,
            id='DeliveryServiceCourierDynamodbTable',
            table_name=self.table_name,
            partition_key=aws_dynamodb.Attribute(name=self.partition_key,
                                                 type=aws_dynamodb.AttributeType.STRING),
            sort_key=aws_dynamodb.Attribute(name=self.sort_key,
                                            type=aws_dynamodb.AttributeType.STRING),
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # DynamoDB GSI for sparce index
        table.add_global_secondary_index(index_name='CourierAvailable',
                                         partition_key=aws_dynamodb.Attribute(
                                                        name='courier_available',
                                                        type=aws_dynamodb.AttributeType.STRING),
                                         sort_key=None,
                                         projection_type=aws_dynamodb.ProjectionType.ALL,
                                         # read_capacity=1,  PAY_PER_REQUESTなので指定できない
                                         # write_capacity=1  PAY_PER_REQUESTなので指定できない
                                         )

        return table


class RestaurantReplicaTableConstructor(Construct):
    def __init__(self, scope: "Construct", id: str) -> None:
        super().__init__(scope, id)
        self.table_name = 'Delivery-RestaurantReplica'
        self.partition_key = 'PK'
        self.sort_key = 'SK'
        self.table = self.create_restaurant_table()

    def create_restaurant_table(self) -> aws_dynamodb.Table:
        table = aws_dynamodb.Table(
            self,
            id='Delivery_RestaurantReplicaDynamodbTable',
            table_name=self.table_name,
            partition_key=aws_dynamodb.Attribute(name=self.partition_key,
                                                 type=aws_dynamodb.AttributeType.STRING),
            sort_key=aws_dynamodb.Attribute(name=self.sort_key,
                                            type=aws_dynamodb.AttributeType.STRING),
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST
        )
        return table
