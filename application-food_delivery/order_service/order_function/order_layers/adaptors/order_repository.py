import os
import abc
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from order_layers.domain import order_model
from order_layers.common import common
from order_layers.adaptors import dynamo_exception as dx
from order_layers.common import exception as ex


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, order: order_model.Order):
        raise NotImplementedError

    @abc.abstractmethod
    def find_by_id(self, order_id) -> order_model.Order:
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    """
    Order Dynamo Item
        PK: ORDER#{order_id}
        SK: METADATA#{order_id}
        lock_version: 1
        order_state: APPROVAL_PENDING
        consumer_id: 1
        order_minimum: {"value": 1000, "currency": "JPN"}
        restaurant_id: 1
        order_line_items: [
                            {
                                "menu_id": "000001",
                                "menu_name": "Curry Rice",
                                "price": {
                                    'value': 800,
                                    'currency': 'JPY'
                                }
                            }
        ]
        delivery_information: {
            "delivery_time": "2022-11-30T05:00:30.001000Z",
            "delivery_address": {
                "street1": "9 Amazing View",
                "street2": "Soi 7",
                "city": "Oakland",
                "state": "CA",
                "zip": "94612"
            }
        }
        payment_information: None  (注)
    """
    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'OrderService')

    def save(self, order: order_model.Order):
        order_dynamo_dict = self.to_dynamo_dict(order)
        with dx.dynamo_exception_check():
            resp = self.client.put_item(TableName=self.table_name,
                                        Item=order_dynamo_dict)

    def find_by_id(self, order_id) -> order_model.Order:
        with dx.dynamo_exception_check():
            resp = self.client.get_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'ORDER#{order_id}'},
                    'SK': {'S': f'METADATA#{order_id}'},
                },
            )

        # if resp['Item'] is None:
        if not resp.get('Item', None):
            raise ex.ItemNotFoundException(f'order_id: {order_id}')

        return self._dynamo_obj_to_order_obj(resp['Item'])

    @staticmethod
    def to_dynamo_dict(order):
        order_dict = order.to_dict()

        # order_idをDynamo PrimaryKeyに変換
        order_dict['PK'] = f"ORDER#{order.order_id}"
        order_dict['SK'] = f"METADATA#{order.order_id}"
        del order_dict['order_id']

        # valueがNoneのものを削除する (MAPなどのnest階層はそのまま)
        without_none = {k: v for k, v in order_dict.items() if v is not None}
        order_dict.clear()
        order_dict.update(without_none)

        serializer = boto3.dynamodb.types.TypeSerializer()
        dynamo_dict = {k: serializer.serialize(v) for k, v in order_dict.items()}
        return dynamo_dict

    @staticmethod
    def _dynamo_obj_to_order_obj(dynamo_item):
        """ DynamoDB obj -> Order Obj """
        deserializer = boto3.dynamodb.types.TypeDeserializer()
        python_obj = {k: deserializer.deserialize(v) for k, v in dynamo_item.items()}
        python_obj['order_id'] = python_obj['PK'].split('#')[1]
        del python_obj['PK']
        del python_obj['SK']
        order = order_model.Order.from_dict(python_obj)
        return order
