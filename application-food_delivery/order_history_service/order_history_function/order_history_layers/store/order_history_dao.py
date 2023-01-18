import os
import abc
import json
import enum
import datetime
import dataclasses
from typing import Optional
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from order_history_layers.model import order_history_model
from order_history_layers.store import dynamo_exception as dx
from order_history_layers.common import exceptions as ex
from order_history_layers.service import events
from order_history_layers.common import json_encoder


# class DeliveryState(enum.Enum):
#     PICKEDUP = 'PICKEDUP'
#     DELIVERED = 'DELIVERED'


class AbstractDao(abc.ABC):
    @abc.abstractmethod
    def save(self,
             order: order_history_model.Order,
             order_event_id: int):  # for Idempotence
        raise NotImplementedError

    @abc.abstractmethod
    def find_by_id(self, order_id) -> order_history_model.Order:
        raise NotImplementedError


class DynamoDbDao(AbstractDao):
    """
    Order Dynamo Item
        PK: ORDER#{order_id}
        SK: METADATA#{order_id}
        order_event_id: 101
        consumer_id: 1  # GSI PK
        restaurant_id: 1
        order_state: APPROVAL_PENDING
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
        creation_date: '2023-01-17T10:35:16.453147Z'  GSI SK  DAOで追加するAttribute
    """
    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'OrderHistory')

    @dataclasses.dataclass
    class OrderHistoryFilter:
        since: Optional[str] = datetime.datetime.strftime(
            datetime.datetime.utcnow() + datetime.timedelta(days=-30), '%Y-%m-%dT%H:%M:%S.%fZ')
        status: Optional[str] = None
        keyword: Optional[str] = None
        start_key_token: Optional[str] = None
        page_size: Optional[int] = None

    def save(self, order: order_history_model.Order, order_event_id):
        order_dynamo_dict = self._to_dynamo_dict(order, order_event_id)
        with dx.dynamo_exception_check():
            resp = self.client.put_item(TableName=self.table_name,
                                        Item=order_dynamo_dict,
                                        ConditionExpression='attribute_not_exists(#order_event_id) OR #order_event_id < :order_event_id',
                                        ExpressionAttributeNames={
                                            '#order_event_id': 'order_event_id',
                                        },
                                        ExpressionAttributeValues={
                                            ':order_event_id': {'N': str(order_event_id)},
                                        })

    def update_order_state(self, event, order_event_id):
        print(f'update_order_state() event: {json.dumps(event.to_dict(), cls=json_encoder.JSONEncoder)}')
        print(f'event: {event.__class__.__name__}')
        """
        {
            "aggregate": "ORDER",
            "aggregate_id": "8555620f791b49c19cc1eca9274b6e99",
            "event_type": "OrderAuthorized",
            "event_id": "66",
            "timestamp": "2023-01-11T10:33:27.824076Z",
            "order_id": "8555620f791b49c19cc1eca9274b6e99"
        }
        """

        # -----------------------
        # Delivery State
        # order_state = event.__class__.__name__  # OrderAuthorized, OrderCancelled, OrderRejected
        event_type = event.__class__.__name__  # DeliveryPickedup, DeliveryDelivered
        if event_type == 'OrderAuthorized':
            order_state = order_history_model.OrderState('APPROVED').value
        elif event_type == 'OrderCancelled':
            order_state = order_history_model.OrderState('CANCELLED').value
        elif event_type == 'OrderRejected':
            order_state = order_history_model.OrderState('REJECTED').value
        else:
            raise Exception(f"NotSupportEvent: {event_type}")

        with dx.dynamo_exception_check():

            resp = self.client.update_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'ORDER#{event.order_id}'},
                    'SK': {'S': f'METADATA#{event.order_id}'},
                },
                UpdateExpression='SET #order_state = :order_state',
                ConditionExpression='attribute_not_exists(#order_event_id) '
                                    'OR #order_event_id < :order_event_id',
                ExpressionAttributeNames={
                    '#order_state': 'order_state',
                    '#order_event_id': 'order_event_id',
                },
                ExpressionAttributeValues={
                    ':order_state': {'S': order_state},
                    ':order_event_id': {'N': str(order_event_id)},
                },
                ReturnValues='NONE',
            )

    def update_delivery_state(self, event, delivery_event_id):
        print(f'update_delivery_state() event: {json.dumps(event.to_dict(), cls=json_encoder.JSONEncoder)}')
        print(f'event: {event.__class__.__name__}')
        # 注:   delivery_idとorder_idは同じ
        """
        {
            "aggregate": "DELIVERY",
            "aggregate_id": "8555620f791b49c19cc1eca9274b6e99",
            "event_type": "DeliveryPickedup",
            "event_id": "68",
            "timestamp": "2023-01-11T10:33:27.824076Z",
            "delivery_id": "8555620f791b49c19cc1eca9274b6e99"
        }
        """

        # Delivery State
        event_type = event.__class__.__name__  # DeliveryPickedup, DeliveryDelivered
        if event_type == 'DeliveryPickedup':
            delivery_state = order_history_model.DeliveryState('PICKEDUP').value
        elif event_type == 'DeliveryDelivered':
            delivery_state = order_history_model.DeliveryState('DELIVERED').value
        else:
            raise Exception(f"NotSupportEvent: {event_type}")

        with dx.dynamo_exception_check():
            resp = self.client.update_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'ORDER#{event.delivery_id}'},  # 注: delivery_idとorder_idは同じ
                    'SK': {'S': f'METADATA#{event.delivery_id}'},  # 注: delivery_idとorder_idは同じ
                },
                UpdateExpression='SET #delivery_state = :delivery_state',
                ConditionExpression='attribute_not_exists(#delivery_event_id) '
                                    'OR #delivery_event_id < :delivery_event_id',
                ExpressionAttributeNames={
                    '#delivery_state': 'delivery_state',
                    '#delivery_event_id': 'delivery_event_id',
                },
                ExpressionAttributeValues={
                    ':delivery_state': {'S': delivery_state},
                    ':delivery_event_id': {'N': str(delivery_event_id)},
                },
                ReturnValues='NONE',
            )

    # Todo: ここから 2023.01.17
    #  この実装のテスト Postmanで・・・
    def find_order_history(
            self,
            consumer_id,
            order_history_filter: OrderHistoryFilter) -> list[order_history_model.Order]:

        print(f'find_order_history() consumer_id: {consumer_id}')
        print(f'find_order_history() since: {order_history_filter.since}')

        with dx.dynamo_exception_check():
            resp = self.client.query(
                TableName=self.table_name,
                IndexName='OrderHistoryByConsumerIdAndCreationTime',
                KeyConditionExpression="consumer_id = :consumer_id AND creation_date > :creation_date",
                ExpressionAttributeValues={
                    ":consumer_id": {"N": f"{consumer_id}"},
                    ":creation_date": {"S": order_history_filter.since},
                },
                ScanIndexForward=False,
            )

        print(f'query() resp: {json.dumps(resp, cls=json_encoder.JSONEncoder)}')

        if not resp.get('Items', None):  # Todo: Itemsが無い場合の対応
            raise ex.ItemNotFoundException(f'consumer_id: {consumer_id}')

        # return self._dynamo_obj_to_order_obj(resp['Item'])
        return [self._dynamo_obj_to_order_obj(item) for item in resp['Items']]

    def find_by_id(self, order_id) -> order_history_model.Order:
        with dx.dynamo_exception_check():
            resp = self.client.get_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'ORDER#{order_id}'},
                    'SK': {'S': f'METADATA#{order_id}'},
                },
            )

        if not resp.get('Item', None):
            raise ex.ItemNotFoundException(f'order_id: {order_id}')

        return self._dynamo_obj_to_order_obj(resp['Item'])

    @staticmethod
    def _to_dynamo_dict(order, order_event_id):
        order_dict = order.to_dict()

        # order_idをDynamo PrimaryKeyに変換
        order_dict['PK'] = f"ORDER#{order.order_id}"
        order_dict['SK'] = f"METADATA#{order.order_id}"
        del order_dict['order_id']

        # for Idempotence
        order_dict['order_event_id'] = order_event_id

        # DynamoDB GSI SK for Sorted Query
        order_dict['creation_date'] = datetime.datetime.strftime(datetime.datetime.utcnow(),
                                                                 '%Y-%m-%dT%H:%M:%S.%fZ')

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
        del python_obj['creation_date']  # DynamoDB GSI SK for Sorted Query
        del python_obj['order_event_id']  # for 冪等性

        order = order_history_model.Order.from_dict(python_obj)
        return order
