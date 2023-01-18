import json
import os
import abc
import uuid
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from delivery_layer.domain import courier_model
from delivery_layer.common import exception as ex
from delivery_layer.adaptors import dynamo_exception as dx


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, courier: courier_model.Courier):
        raise NotImplementedError

    @abc.abstractmethod
    def find_by_id(self, courier_id) -> courier_model.Courier:
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    """

    Courier - Plan -> List[Action]

    Courier Item - Dynamo Item    
        PK: COURIER#{courier_id}    - Number
        SK: METADATA#{courier_id}    - Number
        # "available" DynamoDB Sparse Index
            # available: True/False       - Boolean
            # Trueならuuidがあり、Falseならuuidがない
            # GSI: CourierAvailable
            # SCANで検索
        available: uuid4.hex        - String
        plan: [                     - List[Map]
            {
                'action_type': 'PICKUP',
                'delivery_id': 1,
                'address': {
                    'street1': '1 Main Street',
                    'street2': 'Unit 99',
                    'city': 'Oakland',
                    'state': 'CA',
                    'zip': '94611'
                },
                'time' = '2022-11-30T05:00:30.001000Z'
            },
        ]
        done: [                     - List[Map]
            {
                'action_type': 'PICKUP',
                'delivery_id': 1,
                'address': {
                    'street1': '1 Main Street',
                    'street2': 'Unit 99',
                    'city': 'Oakland',
                    'state': 'CA',
                    'zip': '94611'
                },
                'time' = '2022-11-30T05:00:30.001000Z'
            },
        ]
    """

    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_COURIER_TABLE_NAME', 'Delivery-Courier')

    def create(self, courier: courier_model.Courier):
        courier_dynamo_dict = self.to_dynamo_dict(courier)
        with dx.dynamo_exception_check():
            resp = self.client.put_item(
                TableName=self.table_name,
                Item=courier_dynamo_dict,
                ConditionExpression='attribute_not_exists(PK)',  # 上書き禁止
                # ReturnValues='ALL_NEW',  # Todo: ReturnValues can only be ALL_OLD or NONE
            )

            print(f'courier_repository: create() resp: {resp}')
            return resp

    def save(self, courier: courier_model.Courier):
        courier_dynamo_dict = self.to_dynamo_dict(courier)
        with dx.dynamo_exception_check():
            resp = self.client.put_item(
                TableName=self.table_name,
                Item=courier_dynamo_dict,
                # ConditionExpression='attribute_not_exists(PK)'  # 上書きできるようにする
            )
            return resp

    @staticmethod
    def to_dynamo_dict(courier):
        """
        Courier -> DynamoDB obj
         - available - sparce index
            availableがTrueの場合、courier_available(uuid値)が有り
            availableがFalseの場合、courier_available(uuid値)が無い
            all available courierの取得はscanで行う。
        """
        def without_none(d: dict):
            # valueがNoneのものを削除する (MAPなどのnest階層はそのまま)
            without_none_dict = {k: v for k, v in d.items() if v is not None}
            d.clear()
            d.update(without_none_dict)
            return d

        courier_dict = courier.to_dict()
        courier_dict = without_none(courier_dict)

        print(f'CourierRepo.to_dynamo_dict: courier_dict: {courier_dict}')

        courier_dict['PK'] = f"COURIER#{courier_dict['courier_id']}"
        courier_dict['SK'] = f"METADATA#{courier_dict['courier_id']}"
        del courier_dict['courier_id']
        if courier_dict.get('available', None):  # available: Trueの場合
            courier_dict['courier_available'] = uuid.uuid4().hex
        serializer = boto3.dynamodb.types.TypeSerializer()
        dynamo_dict = {k: serializer.serialize(v) for k, v, in courier_dict.items()}
        return dynamo_dict

    def find_by_id(self, courier_id) -> courier_model.Courier:

        print(f'find_by_id(): courier_id: {courier_id}')

        with dx.dynamo_exception_check():
            resp = self.client.get_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'COURIER#{courier_id}'},
                    'SK': {'S': f'METADATA#{courier_id}'},
                },
            )

        if not resp.get('Item', None):
            raise ex.ItemNotFoundException(f'courier_id: {courier_id}')

        return self._dynamo_obj_to_courier_python_obj(resp['Item'])

    def find_all_available_courier(self):
        """sparce index(courier_available) GSIのscan"""
        with dx.dynamo_exception_check():
            resp = self.client.scan(
                TableName=self.table_name,
                IndexName='CourierAvailable')  # CourierAvailable DynamoDB GSI

        print(f'resp: {resp}')
        if not resp.get('Items', None):
            raise ex.AvailableCourierNotFoundException('CourierAvailable GSI - Space Index')

        couriers = [self._dynamo_obj_to_courier_python_obj(item) for item in resp['Items']]
        return couriers

    @staticmethod
    def _dynamo_obj_to_courier_python_obj(dynamo_item):
        """ DynamoDB obj -> Courier Obj """
        deserializer = boto3.dynamodb.types.TypeDeserializer()
        python_obj = {k: deserializer.deserialize(v) for k, v in dynamo_item.items()}
        python_obj['courier_id'] = int(python_obj['PK'].split('#')[1])
        del python_obj['PK']
        del python_obj['SK']
        if python_obj.get('courier_available', None):
            # sparce index (available) の対応
            # - 'courier_available'はdomain modelではなくDynamoDB Sparse Index。削除する
            del python_obj['courier_available']

        courier = courier_model.Courier.from_dict(python_obj)
        return courier
