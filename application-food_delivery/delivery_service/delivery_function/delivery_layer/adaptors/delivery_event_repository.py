import os
import abc
import datetime
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from delivery_layer.service import domain_event_envelope
from delivery_layer.adaptors import dynamo_exception as dx


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, event: domain_event_envelope.DomainEventEnvelope):
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    """
    Order Domain Event - Dynamo Item
        PK: DELIVERY#{delivery_id}
        SK: EVENTTYPE#DeliveryPickedup#EVENTID#(1cc9e8508c82469299a0193572d57c73}
    """

    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_EVENT_TABLE_NAME', 'DeliveryEvent')

    def save(self, event: domain_event_envelope.DomainEventEnvelope):

        event_dict = self.to_dynamo_dict(event)

        with dx.dynamo_exception_check():
            resp = self.client.put_item(TableName=self.table_name,
                                        Item=event_dict)

        return event_dict['event_id']
        # Todo: CQRSのレイテンシーがあるため、REST API Clientがpollingするidとして使えるようにリターンする。
        #  現段階ではREST APIのresultには入れてない。

    def to_dynamo_dict(self, domain_event):
        """
        PK: DELIVERY#8a4347b048034e80bfa45a5d70c8f301      [aggregate]#[delivery_id]
        SK: EVENTTYPE#DeliveryPickedup#EVENTID#1234        EVENTTYPE#[event_name]#EVNTID#[event_id]
        timestamp: '2022-11-30T05:00:30.001000Z'
        ...Event Data
        """

        # Domain Event Dataの抽出
        event_dict = domain_event.domain_event.to_dict()

        # Event Envelopeの抽出
        event_id = self._get_sequential_event_id()
        timestamp = datetime.datetime.strftime(datetime.datetime.utcnow(),
                                               '%Y-%m-%dT%H:%M:%S.%fZ')
        event_dict['PK'] = f"{domain_event.aggregate}#{domain_event.domain_event.delivery_id}"
        event_dict['SK'] = f'EVENTTYPE#{domain_event.domain_event.__class__.__name__}' \
                           f'#EVENTID#{event_id}'

        # for Event Envelope
        event_dict['timestamp'] = timestamp
        event_dict['event_id'] = event_id

        # DynamoDBシリアライズ
        serializer = boto3.dynamodb.types.TypeSerializer()
        item = {k: serializer.serialize(v) for k, v in event_dict.items()}

        # 不要なものを削除
        # del event_dict['delivery_id']

        return item

    def _get_sequential_event_id(self) -> int:
        with dx.dynamo_exception_check():
            resp = self.client.update_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': 'IDCOUNTER#EVENT'},
                    'SK': {'S': 'IDCOUNTER#EVENT'},
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
        new_id = int(resp['Attributes']['id_count']['N'])
        return new_id
