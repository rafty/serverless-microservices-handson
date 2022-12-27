import decimal
import os
import abc
import uuid
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError
from kitchen_layer.domain import ticket_model
from kitchen_layer.domain import kitchen_domain_event
from kitchen_layer.adaptors import dynamo_exception as dx


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, event: kitchen_domain_event.DomainEvent):
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_EVENT_TABLE_NAME', 'KitchenEvent')

    def save(self, events: list[kitchen_domain_event.DomainEvent]):
        print(f'kitchen_event_repository.py save(): {events}')
        """
        TicketCreated Domain Event
            PK=TICKET#{ticket_id}
            SK=CHANNEL#TicketCreated#EVENTID#(1cc9e8508c82469299a0193572d57c73}
            restaurant_id  1
            line_items: [
                            {
                                "menu_id": "000001",
                                "name": "Curry Rice",
                                "quantity": 2
                            },
                            {
                                "menu_id": "000002",
                                "name": "Hamburger",
                                "quantity": 1
                            },
                            {
                                "menu_id": "000003",
                                "name": "Ramen",
                                "quantity": 1
                            }
                        ]
        """
        """
        以下の構成をやめた
        - TicketCreated Domain Event -
            PK=CHANNEL#TicketCreated    'S'
            SK=EVENTID#{UUID.HEX}       'S'
            ticket_id                   'N'
            restaurant_id               'N'
            line_items                  LIST[MAP]
        """
        if len(events):
            event_list = self.to_dynamo_dict_list(events)
            items = self.to_batch_write_items(event_list)
            with dx.dynamo_exception_check():
                resp = self.client.batch_write_item(
                    RequestItems={
                        self.table_name: items
                    }
                )

    @staticmethod
    def to_dynamo_dict_list(events: list[kitchen_domain_event.DomainEvent]):
        print(f'kitchen_event_repository.py to_dynamo_dict_list(): {events}')

        def to_dynamo_dict(event):
            event_dict = event.to_dict()
            event_dict['PK'] = f"TICKET#{event.ticket_id}"
            event_dict['SK'] = f'CHANNEL#{event.__class__.__name__}#EVENTID#{event.event_id}'
            serializer = boto3.dynamodb.types.TypeSerializer()
            item = {k: serializer.serialize(v) for k, v in event_dict.items()}
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
