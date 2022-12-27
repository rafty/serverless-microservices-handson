import decimal
import os
import abc
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError
from account_layers.domain import domain_event
from account_layers.adaptors import dynamo_exception as dx


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, events: list[domain_event.DomainEvent]):
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    """
    Consumer Domain Event - Dynamo Item
        PK: ACCOUNT#{account_id}
        SK: CHANNEL#AccountCreated#EVENTID#(1cc9e8508c82469299a0193572d57c73}
        consumer_id: 1
    """

    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_EVENT_TABLE_NAME', 'AccountEvent')

    def save(self, events: list[domain_event.DomainEvent]):

        event_dict_list = self.to_dynamo_dict_list(events)
        items = self.to_batch_write_items(event_dict_list)
        with dx.dynamo_exception_check():
            resp = self.client.batch_write_item(
                RequestItems={
                    self.table_name: items
                }
            )

    @staticmethod
    def to_dynamo_dict_list(events: list[domain_event.DomainEvent]):

        def to_dynamo_dict(event):
            event_dict = event.to_dict()
            event_dict['PK'] = f"ACCOUNT#{event.account_id}"
            event_dict['SK'] = f'CHANNEL#{event.__class__.__name__}#EVENTID#{event.event_id}'
            serializer = boto3.dynamodb.types.TypeSerializer()
            item = {k: serializer.serialize(v) for k, v in event_dict.items()}
            # del event_dict['consumer_id']
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
