import os
import abc
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from consumer_layers.domain import consumer_model
from consumer_layers.adaptors import dynamo_exception as dx
from consumer_layers.common import exceptions as ex


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, consumer: consumer_model.Consumer):
        raise NotImplementedError

    @abc.abstractmethod
    def find_by_id(self, consumer_id) -> consumer_model.Consumer:
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    """
    DynamoDB Table Construction
        PK: CONSUMER#{consumer_id}
        SK: METADATA#{consumer_id}
        name: {
            "first_name": "Takashi",
            "last_name": "Yagita",
        }
    """

    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'ConsumerService')

    def get_unique_consumer_id(self) -> int:
        with dx.dynamo_exception_check():
            resp = self.client.update_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': 'IDCOUNTER#Consumer'},
                    'SK': {'S': 'IDCOUNTER#Consumer'},
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

        new_consumer_id = int(resp['Attributes']['id_count']['N'])
        return new_consumer_id

    def save(self, consumer: consumer_model.Consumer):
        consumer_dynamo_dict = self.to_dynamo_dict(consumer)
        with dx.dynamo_exception_check():
            resp = self.client.put_item(TableName=self.table_name,
                                        Item=consumer_dynamo_dict)

    def find_by_id(self, consumer_id) -> consumer_model.Consumer:
        with dx.dynamo_exception_check():
            resp = self.client.get_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'CONSUMER#{consumer_id}'},
                    'SK': {'S': f'METADATA#{consumer_id}'},
                },
            )

        print(f'consumer_repo.find_by_id(): resp: {resp}')
        # if resp['Item'] is None:
        if not resp.get('Item', None):
            raise ex.ItemNotFoundException(f'ItemNotFoundException consumer_id: {consumer_id}')

        return self._dynamo_obj_to_consumer_obj(resp['Item'])

    @staticmethod
    def to_dynamo_dict(consumer):
        consumer_dict = consumer.to_dict()
        consumer_dict['PK'] = f"CONSUMER#{consumer.consumer_id}"
        consumer_dict['SK'] = f"METADATA#{consumer.consumer_id}"
        del consumer_dict['consumer_id']

        # valueがNoneのものを削除する (MAPなどのnest階層はそのまま)
        without_none = {k: v for k, v in consumer_dict.items() if v is not None}
        consumer_dict.clear()
        consumer_dict.update(without_none)

        serializer = boto3.dynamodb.types.TypeSerializer()
        dynamo_dict = {k: serializer.serialize(v) for k, v in consumer_dict.items()}
        return dynamo_dict

    @staticmethod
    def _dynamo_obj_to_consumer_obj(dynamo_item):
        """ DynamoDB obj -> Consumer Obj """
        deserializer = boto3.dynamodb.types.TypeDeserializer()
        python_obj = {k: deserializer.deserialize(v) for k, v in dynamo_item.items()}
        python_obj['consumer_id'] = python_obj['PK'].split('#')[1]
        del python_obj['PK']
        del python_obj['SK']
        consumer = consumer_model.Consumer.from_dict(python_obj)
        return consumer
