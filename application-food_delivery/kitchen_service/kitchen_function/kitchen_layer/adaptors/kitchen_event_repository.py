import os
import abc
import datetime
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from kitchen_layer.domain import kitchen_domain_event
from kitchen_layer.adaptors import dynamo_exception as dx
from kitchen_layer.service.domain_event_envelope import DomainEventEnvelope


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    # def save(self, event: kitchen_domain_event.DomainEvent):
    def save(self, event: DomainEventEnvelope):
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_EVENT_TABLE_NAME', 'KitchenEvent')

    def save(self, event: list[kitchen_domain_event.DomainEvent]):
        print(f'kitchen_event_repository.py save(): {event}')
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
        # if len(events):
        #     event_list = self.to_dynamo_dict_list(events)
        #     items = self.to_batch_write_items(event_list)
        #     with dx.dynamo_exception_check():
        #         resp = self.client.batch_write_item(
        #             RequestItems={
        #                 self.table_name: items
        #             }
        #         )
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
        timestamp = datetime.datetime.strftime(datetime.datetime.utcnow(),
                                               '%Y-%m-%dT%H:%M:%S.%fZ')

        event_dict['PK'] = f"{event.aggregate}#{event.domain_event.ticket_id}"
        event_dict['SK'] = f'EVENTTYPE#{event.domain_event.__class__.__name__}' \
                           f'#EVENTID#{event_id}'

        # for Event Envelope
        event_dict['timestamp'] = timestamp
        event_dict['event_id'] = event_id

        # DynamoDBシリアライズ
        serializer = boto3.dynamodb.types.TypeSerializer()
        item = {k: serializer.serialize(v) for k, v in event_dict.items()}
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
    # def to_dynamo_dict_list(events: list[kitchen_domain_event.DomainEvent]):
    #     print(f'kitchen_event_repository.py to_dynamo_dict_list(): {events}')
    #
    #     def to_dynamo_dict(event):
    #         event_dict = event.to_dict()
    #         event_dict['PK'] = f"TICKET#{event.ticket_id}"
    #         event_dict['SK'] = f'CHANNEL#{event.__class__.__name__}#EVENTID#{event.event_id}'
    #         serializer = boto3.dynamodb.types.TypeSerializer()
    #         item = {k: serializer.serialize(v) for k, v in event_dict.items()}
    #         return item
    #
    #     event_list = [to_dynamo_dict(event) for event in events]
    #     return event_list
    #
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
