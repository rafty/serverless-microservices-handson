import decimal
import os
import abc
import uuid
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError
from restaurant_layers.domain import restaurant_model
from restaurant_layers.domain import restaurant_domain_events
from restaurant_layers.adaptors import dynamo_exception as dx


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, events: list[restaurant_domain_events.DomainEvent]):
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    """
    Restaurant Event - Dynamo Item
        --- Restaurant Metadata ---
        PK: RESTAURANT#{restaurant_id}
        SK: CHANNEL#RestaurantCreated#EVENTID#(1cc9e8508c82469299a0193572d57c73}
        restaurant_name: 'Ajenta'
        restaurant_address: {
            'street1': '9 Amazing View',
            'street2': 'Soi 8',
            'city': 'Oakland',
            'state': 'CA',
            'zip': '94612'
        }
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
        self.table_name = os.environ.get('DYNAMODB_EVENT_TABLE_NAME', 'RestaurantEvent')

    def save(self, events: list[restaurant_domain_events.DomainEvent]):
        event_dict_list = self.to_dynamo_dict_list(events)
        items = self.to_batch_write_items(event_dict_list)
        with dx.dynamo_exception_check():
            resp = self.client.batch_write_item(
                RequestItems={
                    self.table_name: items
                }
            )

    @staticmethod
    def to_dynamo_dict_list(events: list[restaurant_domain_events.DomainEvent]):

        def to_dynamo_dict(event):
            event_dict = event.to_dict()
            event_dict['PK'] = f"RESTAURANT#{event.restaurant_id}"
            event_dict['SK'] = f'CHANNEL#{event.__class__.__name__}#EVENTID#{event.event_id}'
            serializer = boto3.dynamodb.types.TypeSerializer()
            item = {k: serializer.serialize(v) for k, v in event_dict.items()}
            del event_dict['restaurant_id']
            return item

        event_list = [to_dynamo_dict(event) for event in events]
        return event_list

    @staticmethod
    def to_batch_write_items(items):

        def to_put_item(item):
            return {
                'PutRequest': {
                    'Item': item
                },
            }

        batch_items = [to_put_item(item) for item in items]
        return batch_items


