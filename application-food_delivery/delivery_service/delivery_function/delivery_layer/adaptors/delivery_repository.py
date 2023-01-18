import json
import os
import abc
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from delivery_layer.domain import delivery_model
from delivery_layer.adaptors import dynamo_exception as dx
from delivery_layer.common import exception as ex
from delivery_layer.common import json_encoder

class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, delivery: delivery_model.Delivery):
        raise NotImplementedError

    @abc.abstractmethod
    def find_by_id(self, delivery_id) -> delivery_model.Delivery:
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    """
    Delivery - Dynamo Item
        PK: DELIVERY#{delivery_id}
        SK: METADATA#{delivery_id}
        state: PENDING
        pickup_address: {
            "street1": "1 Main Street",
            "street2": "Unit 99",
            "city": "Oakland",
            "state": "CA",
            "zip": "94611"
        }
        delivery_address: {
            "street1": "1 Main Street",
            "street2": "Unit 99",
            "city": "Oakland",
            "state": "CA",
            "zip": "94611"
        }
        restaurant_id: 1
        pickup_time: "2022-11-30T05:00:30.001000Z"
        delivery_time: "2022-11-30T05:00:30.001000Z"
        ready_by: "2022-11-30T05:00:30.001000Z"
        assigned_courier: 1
    """

    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'DeliveryService')

    def save(self, delivery: delivery_model.Delivery):
        print(f'delivery_repo.save() delivery: {delivery}')

        delivery_dynamo_dict = self.to_dynamo_dict(delivery)

        print(f'delivery_dynamo_dict: {json.dumps(delivery_dynamo_dict, cls=json_encoder.JSONEncoder)}')

        with dx.dynamo_exception_check():
            resp = self.client.put_item(TableName=self.table_name,
                                        Item=delivery_dynamo_dict)

    @staticmethod
    def to_dynamo_dict(delivery):

        def without_none(d: dict):
            # valueがNoneのものを削除する (MAPなどのnest階層はそのまま)
            without_none_dict = {k: v for k, v in d.items() if v is not None}
            d.clear()
            d.update(without_none_dict)
            return d

        delivery_dict = delivery.to_dict()
        delivery_dict = without_none(delivery_dict)
        delivery_dict['PK'] = f"DELIVERY#{delivery.delivery_id}"
        delivery_dict['SK'] = f"METADATA#{delivery.delivery_id}"
        serializer = boto3.dynamodb.types.TypeSerializer()
        item = {k: serializer.serialize(v) for k, v in delivery_dict.items()}
        del delivery_dict['delivery_id']
        return item

    def find_by_id(self, delivery_id) -> delivery_model.Delivery:
        with dx.dynamo_exception_check():
            resp = self.client.get_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'DELIVERY#{delivery_id}'},
                    'SK': {'S': f'METADATA#{delivery_id}'},
                }
            )

        if not resp.get('Item', None):
            raise ex.ItemNotFoundException(f'delivery_id: {delivery_id}')

        return self._dynamo_obj_to_delivery_python_obj(resp['Item'])

    @staticmethod
    def _dynamo_obj_to_delivery_python_obj(dynamo_item):
        """ DynamoDB obj -> delivery Obj """
        deserializer = boto3.dynamodb.types.TypeDeserializer()
        python_obj = {k: deserializer.deserialize(v) for k, v in dynamo_item.items()}
        python_obj['delivery_id'] = python_obj['PK'].split('#')[1]
        del python_obj['PK']
        del python_obj['SK']

        print(f'_dynamo_obj_to_delivery_python_obj() python_obj: {python_obj}')

        delivery = delivery_model.Delivery.from_dict(python_obj)

        return delivery
