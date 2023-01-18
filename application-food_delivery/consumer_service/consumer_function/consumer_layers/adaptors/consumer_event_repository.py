import decimal
import os
import abc
import datetime
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from consumer_layers.domain import domain_events
from consumer_layers.service.domain_event_envelope import DomainEventEnvelope
from consumer_layers.adaptors import dynamo_exception as dx


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, event: domain_events.DomainEvent):
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    """
    Consumer Domain Event - Dynamo Item
        PK: CONSUMER#{consumer_id}
        SK: EVENTTYPE#ConsumerCreated#EVENTID#(1cc9e8508c82469299a0193572d57c73}
        name: {
            "first_name": "Takashi",
            "last_name": "Yagita",
        }
    """

    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_EVENT_TABLE_NAME', 'ConsumerEvent')

    def save(self, event: DomainEventEnvelope):

        # event_dict_list = self.to_dynamo_dict_list(events)
        # items = self.to_batch_write_items(event_dict_list)
        # with dx.dynamo_exception_check():
        #     resp = self.client.batch_write_item(
        #         RequestItems={
        #             self.table_name: items
        #         }
        #     )
        event_dict = self.to_dynamo_dict(event)

        with dx.dynamo_exception_check():
            resp = self.client.put_item(TableName=self.table_name,
                                        Item=event_dict)

        return event_dict['event_id']
        # Todo: CQRSのレイテンシーがあるため、REST API Clientがpollingするidとして使えるようにリターンする。
        #  現段階ではREST APIのresultには入れてない。

    def to_dynamo_dict(self, event):
        event_dict = event.domain_event.to_dict()

        # Event Envelopeの抽出
        event_id = self._get_sequential_event_id()
        timestamp = datetime.datetime.strftime(datetime.datetime.utcnow(), '%Y-%m-%dT%H:%M:%S.%fZ')

        event_dict['PK'] = f"{event.aggregate}#{event.domain_event.consumer_id}"
        event_dict['SK'] = f'EVENTTYPE#{event.domain_event.__class__.__name__}' \
                           f'#EVENTID#{event_id}'

        # for Event Envelope
        event_dict['timestamp'] = timestamp
        event_dict['event_id'] = event_id

        # DynamoDBシリアライズ
        serializer = boto3.dynamodb.types.TypeSerializer()
        item = {k: serializer.serialize(v) for k, v in event_dict.items()}
        # del event_dict['consumer_id']
        return item

    def _get_sequential_event_id(self) -> int:
        with dx.dynamo_exception_check():
            resp = self.client.update_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': 'IDCOUNTER#EVENT'},
                    'SK': {'S': 'IDCOUNTER#EVENT'},
                },
                # UpdateExpression='SET #id_count = #id_count + :incr',
                UpdateExpression='SET #id_count = if_not_exists(#id_count, :default) + :incr',
                # Todo: itemがあれば+1更新、itemがなければif_not_exists()で:default値を初期値とする。
                ExpressionAttributeNames={
                  '#id_count': 'id_count',
                },
                ExpressionAttributeValues={
                    ':incr': {'N': '1'},
                    ':default': {'N': '0'}
                },
                ReturnValues='UPDATED_NEW',
            )
        new_consumer_id = int(resp['Attributes']['id_count']['N'])
        return new_consumer_id

    # @staticmethod
    # def to_batch_write_items(items):
    #
    #     def to_put_item(item):
    #         return {
    #             'PutRequest': {
    #                 'Item': item
    #             },
    #         }
    #
    #     batch_items = [to_put_item(item) for item in items]
    #     return batch_items


