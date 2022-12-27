import os
import abc
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from account_layers.domain import account_model
from account_layers.adaptors import dynamo_exception as dx
from account_layers.common import exceptions as ex


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, account: account_model.Account):
        raise NotImplementedError

    @abc.abstractmethod
    def find_by_id(self, consumer_id) -> account_model.Account:
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    """
    DynamoDB Table Construction
        PK: CONSUMER#{consumer_id}
        SK: ACCOUNT#{account_id}
        card_information: {
            "card_number": "1234123412341234",
            "expiry_date": "2024-12-31T23:59:59.999999Z",
        }
    """

    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'AccountService')

    def save(self, account: account_model.Account):
        account_dynamo_dict = self.to_dynamo_dict(account)
        with dx.dynamo_exception_check():
            resp = self.client.put_item(TableName=self.table_name,
                                        Item=account_dynamo_dict)

    def find_by_id(self, consumer_id) -> account_model.Account:
        with dx.dynamo_exception_check():
            resp = self.client.query(
                TableName=self.table_name,
                KeyConditionExpression='PK = :pk AND SK BETWEEN :account_first AND :account_end',
                ExpressionAttributeValues={
                    ':pk': {'S': f'CONSUMER#{consumer_id}'},
                    ':account_first': {'S': 'ACCOUNT#'},
                    ':account_end': {'S': 'ACCOUNT$'},  # 最後まで取得したいから$にしてる
                },
                ScanIndexForward=True
            )

        print(f'account_repo.find_by_id(): resp: {resp}')
        # if resp['Items'] is None:
        if not resp.get('Items', None):
            raise ex.ItemNotFoundException(f'ItemNotFoundException consumer_id: {consumer_id}')

        # Todo: 1 Consumerあたり複数Accountに対応すること。
        #  現在はOne Account per One Consumer
        return self._dynamo_obj_to_account_obj(resp['Items'][0])

    @staticmethod
    def to_dynamo_dict(account):
        account_dict = account.to_dict()  # いまここ
        account_dict['PK'] = f"CONSUMER#{account.consumer_id}"
        account_dict['SK'] = f"ACCOUNT#{account.account_id}"
        # del account_dict['consumer_id']

        # valueがNoneのものを削除する (MAPなどのnest階層はそのまま)
        without_none = {k: v for k, v in account_dict.items() if v is not None}
        account_dict.clear()
        account_dict.update(without_none)

        serializer = boto3.dynamodb.types.TypeSerializer()
        dynamo_dict = {k: serializer.serialize(v) for k, v in account_dict.items()}
        return dynamo_dict

    @staticmethod
    def _dynamo_obj_to_account_obj(dynamo_item):
        """ DynamoDB obj -> Account Obj """
        deserializer = boto3.dynamodb.types.TypeDeserializer()
        python_obj = {k: deserializer.deserialize(v) for k, v in dynamo_item.items()}
        python_obj['consumer_id'] = python_obj['PK'].split('#')[1]
        python_obj['account_id'] = python_obj['SK'].split('#')[1]
        del python_obj['PK']
        del python_obj['SK']
        account = account_model.Account.from_dict(python_obj)
        return account
