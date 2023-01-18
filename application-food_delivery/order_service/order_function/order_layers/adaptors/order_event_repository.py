import os
import abc
import datetime
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from order_layers.domain import order_domain_events
from order_layers.service import domain_event_envelope
from order_layers.adaptors import dynamo_exception as dx


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, event: domain_event_envelope.DomainEventEnvelope):
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    """
    Order Domain Event - Dynamo Item
        PK: ORDER#{order_id}
        SK: EVENTTYPE#OrdderCreated#EVENTID#(1cc9e8508c82469299a0193572d57c73}
        order_details: {
                           'consumer_id': 1,
                           'restaurant_id: 1,
                           'order_line_items': [
                                                 {
                                                    "menu_id": "000001",
                                                    "menu_name": "Curry Rice",
                                                    "price": {
                                                        'value': 800,
                                                        'currency': 'JPY'
                                                    },
                                                    "quantity": 3
                                                 },
                                               ]
                           'order_total': {
                                            'value': 3800,
                                            'currency': 'JPY'
                                          }
                       }
        delivery_information: {
                                "delivery_time": "2022-11-30T05:00:30.001000Z",
                                "delivery_address": {
                                                        'street1': '9 Amazing View',
                                                        'street2': 'Soi 8',
                                                        'city': 'Oakland',
                                                        'state': 'CA',
                                                        'zip': '94612'
                                                    }
                              }
    """

    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_EVENT_TABLE_NAME', 'OrderEvent')

    # def save(self, events: list[order_domain_events.DomainEvent]):
    def save(self, event: domain_event_envelope.DomainEventEnvelope):

        # Todo: eventsからeventに変更したため、batch_write() -> put_item()に変更
        # event_dict_list = self.to_dynamo_dict_list(event)
        # items = self._to_batch_write_items(event_dict_list)
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

    def to_dynamo_dict(self, domain_event):
        """
        PK: ORDER#8a4347b048034e80bfa45a5d70c8f301      [aggregate]#[order_id]
        SK: EVENTTYPE#OrderCreated#EVENTID#1234         EVENTTYPE#[event_name]#EVNTID#[event_id]
        timestamp: '2022-11-30T05:00:30.001000Z'
        ...Event Data
        """
        # Domain Event Dataの抽出
        # DomainEventEnvelope.domain_event -> event_dict
        event_dict = domain_event.domain_event.to_dict()

        # Event Envelopeの抽出
        event_id = self._get_sequential_event_id()
        timestamp = datetime.datetime.strftime(datetime.datetime.utcnow(),
                                               '%Y-%m-%dT%H:%M:%S.%fZ')
        event_dict['PK'] = f"{domain_event.aggregate}#{domain_event.domain_event.order_id}"
        event_dict['SK'] = f'EVENTTYPE#{domain_event.domain_event.__class__.__name__}' \
                           f'#EVENTID#{event_id}'

        # for Event Envelope
        event_dict['timestamp'] = timestamp
        event_dict['event_id'] = event_id

        # DynamoDBシリアライズ
        serializer = boto3.dynamodb.types.TypeSerializer()
        item = {k: serializer.serialize(v) for k, v in event_dict.items()}

        # 不要なものを削除
        # del event_dict['order_id']

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


    # def to_dynamo_dict_list(self, events: list[domain_event_envelope.DomainEventEnvelope]):
    #     def to_dynamo_dict(event):
    #         """
    #         PK: ORDER#8a4347b048034e80bfa45a5d70c8f301      [aggregate]#[order_id]
    #         SK: EVENTTYPE#OrderCreated#EVENTID#1234         EVENTTYPE#[event_name]#EVNTID#[event_id]
    #         timestamp: '2022-11-30T05:00:30.001000Z'
    #         ...Event Data
    #         """
    #
    #         # Domain Event Dataの抽出
    #         # DomainEventEnvelope.domain_event -> event_dict
    #         event_dict = event.domain_event.to_dict()
    #
    #         # Event Envelopeの抽出
    #         event_id = self._get_sequential_event_id()
    #         timestamp = datetime.datetime.strftime(datetime.datetime.utcnow(),
    #                                                '%Y-%m-%dT%H:%M:%S.%fZ')
    #         event_dict['PK'] = f"{event.aggregate}#{event.domain_event.order_id}"
    #         event_dict['SK'] = f'EVENTTYPE#{event.domain_event.__class__.__name__}' \
    #                            f'#EVENTID#{event_id}'
    #         event_dict['timestamp'] = timestamp
    #
    #         # DynamoDBシリアライズ
    #         serializer = boto3.dynamodb.types.TypeSerializer()
    #         item = {k: serializer.serialize(v) for k, v in event_dict.items()}
    #
    #         # 不要なものを削除
    #         # del event_dict['order_id']
    #
    #         return item
    #
    #     event_list = [to_dynamo_dict(event) for event in events]
    #     return event_list


    # @staticmethod
    # def _to_batch_write_items(items):
    #     def to_put_item(item):
    #         return {
    #             'PutRequest': {
    #                 'Item': item
    #             },
    #         }
    #     batch_items = [to_put_item(item) for item in items]
    #     return batch_items
