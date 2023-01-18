import os
import abc
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from kitchen_layer.domain import restaurant_model
from kitchen_layer.adaptors import dynamo_exception as dx
from kitchen_layer.common import exceptions as ex


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, restaurant: restaurant_model.Restaurant, event_id, timestamp):
        raise NotImplementedError

    @abc.abstractmethod
    def find_by_id(self, restaurant_id) -> restaurant_model.Restaurant:
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    """
    Restaurant - Dynamo Item
        --- Restaurant Event ---
        PK: RESTAURANT#{restaurant_id}
        SK: METADATA#{restaurant_id}  # 冪等性が保たれる
        restaurant_id: 1
        menu_items: [
                        {
                            "menu_id": "000001",
                            "menu_name": "Curry Rice",
                            "price": {
                                'value': 800,
                                'currency': 'JPY'
                        },
                    ]
    """
    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_RESTAURANT_REPLICA_TABLE_NAME',
                                         'Kitchen-RestaurantReplica')

    def save(self, restaurant: restaurant_model.Restaurant, event_id, timestamp):
        restaurant_dynamo_dict = self.to_dynamo_dict(restaurant, event_id, timestamp)
        with dx.dynamo_exception_check():
            resp = self.client.put_item(
                TableName=self.table_name,
                Item=restaurant_dynamo_dict,
                ConditionExpression='attribute_not_exists(#event_id) OR #event_id < :event_id',
                ExpressionAttributeNames={
                    '#event_id': 'event_id',
                },
                ExpressionAttributeValues={
                    ':event_id': {'N': str(event_id)},
                }
            )
            # ConditionExpression: 冪等性、古いEventで上書きしない。

    @staticmethod
    def to_dynamo_dict(restaurant, event_id, timestamp):
        restaurant_dict = restaurant.to_dict()

        # primary key
        restaurant_dict['PK'] = f"RESTAURANT#{restaurant.restaurant_id}"
        restaurant_dict['SK'] = f"METADATA#{restaurant.restaurant_id}"

        # for event envelope
        restaurant_dict['event_id'] = event_id
        restaurant_dict['timestamp'] = timestamp

        serializer = boto3.dynamodb.types.TypeSerializer()
        item = {k: serializer.serialize(v) for k, v in restaurant_dict.items()}
        del restaurant_dict['restaurant_id']
        return item

    def find_by_id(self, restaurant_id) -> restaurant_model.Restaurant:
        with dx.dynamo_exception_check():
            resp = self.client.get_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'RESTAURANT#{restaurant_id}'},
                    'SK': {'S': f'METADATA#{restaurant_id}'},
                },
            )

        if not resp.get('Item', None):
            raise ex.ItemNotFoundException(f'restaurant_id: {restaurant_id}')

        return self._dynamo_obj_to_ticket_python_obj(resp['Item'])

    @staticmethod
    def _dynamo_obj_to_ticket_python_obj(dynamo_item):
        """ DynamoDB obj -> Restaurant Obj """
        deserializer = boto3.dynamodb.types.TypeDeserializer()
        python_obj = {k: deserializer.deserialize(v) for k, v in dynamo_item.items()}
        python_obj['restaurant_id'] = int(python_obj['PK'].split('#')[1])
        del python_obj['PK']
        del python_obj['SK']
        restaurant = restaurant_model.Restaurant.from_dict(python_obj)
        return restaurant
