import decimal
import os
import abc
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError
from restaurant_layers.domain import restaurant_model
from restaurant_layers.adaptors import dynamo_exception as dx
from restaurant_layers.common import exception as ex


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, restaurant: restaurant_model.Restaurant):
        raise NotImplementedError

    @abc.abstractmethod
    def find_by_id(self, consumer_id) -> restaurant_model.Restaurant:
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    """
    Restaurant ID  Counter - Dynamo Item
        PK: IDCOUNTER#Restaurant
        SK: IDCOUNTER#Restaurant
        id_count: 0

    Restaurant Item - Dynamo Item
        PK: RESTAURANTID#{restaurant_id}
        SK: METADATA#{restaurant_id}
        restaurant_name: 'Skylark'
        restaurant_address: {
                                'street1': '1 Main Street',
                                'street2': 'Unit 99',
                                'city': 'Oakland',
                                'state': 'CA',
                                'zip': '94611'
                            }
        menu_items: [
                        {
                            'menu_id': '000001',
                            'menu_name': 'Curry Rice',
                            'price': {
                                'value': 800,
                                'currency': 'JPY'
                            }
                        },
                        {
                            'menu_id': '000002',
                            'menu_name': 'Hamburger',
                            'price': {
                                'value': 1000,
                                'currency': 'JPY'
                            }
                        },
                        {
                            'menu_id': '000003',
                            'menu_name': 'Ramen',
                            'price': {
                                'value': 700,
                                'currency': 'JPY'
                            }
                        }
                    ]
    """
    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'RestaurantService')

    def get_unique_restaurant_id(self) -> int:
        with dx.dynamo_exception_check():
            resp = self.client.update_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': 'IDCOUNTER#Restaurant'},
                    'SK': {'S': 'IDCOUNTER#Restaurant'},
                },
                UpdateExpression='SET #id_count = if_not_exists(#id_count, :default) + :incr',
                # itemがあれば+1更新、itemがなければif_not_exists()で:default値を初期値とする。
                ExpressionAttributeNames={
                  '#id_count': 'id_count',
                },
                ExpressionAttributeValues={
                    ':incr': {'N': '1'},
                    ':default': {'N': '0'}
                },
                ReturnValues='UPDATED_NEW',
            )

        new_restaurant_id = int(resp['Attributes']['id_count']['N'])
        return new_restaurant_id

    def save(self, restaurant: restaurant_model.Restaurant):
        restaurant_dynamo_dict = self.to_dynamo_dict(restaurant)
        with dx.dynamo_exception_check():
            resp = self.client.put_item(TableName=self.table_name,
                                        Item=restaurant_dynamo_dict)

    @staticmethod
    def to_dynamo_dict(restaurant):
        restaurant_dict = restaurant.to_dict()
        restaurant_dict['PK'] = f"RESTAURANT#{restaurant.restaurant_id}"
        restaurant_dict['SK'] = f"METADATA#{restaurant.restaurant_id}"
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

        # if resp['Item'] is None:
        if not resp.get('Item', None):
            raise ex.ItemNotFoundException(f'restaurant_id: {restaurant_id}')

        return self._dynamo_obj_to_ticket_python_obj(resp['Item'])

    @staticmethod
    def _dynamo_obj_to_ticket_python_obj(dynamo_item):
        """ DynamoDB obj -> Restaurant Obj """
        deserializer = boto3.dynamodb.types.TypeDeserializer()
        python_obj = {k: deserializer.deserialize(v) for k, v in dynamo_item.items()}
        # Primary Keyの変更: PK, SKをticket attributeに変換
        python_obj['restaurant_id'] = int(python_obj['PK'].split('#')[1])
        del python_obj['PK']
        del python_obj['SK']

        restaurant = restaurant_model.Restaurant.from_dict(python_obj)
        return restaurant


