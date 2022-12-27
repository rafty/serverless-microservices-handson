import json
import os
import abc
import boto3
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from kitchen_layer.domain import ticket_model
from kitchen_layer.common import common
from kitchen_layer.adaptors import dynamo_exception as dx
from kitchen_layer.common import exceptions as ex


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, ticket: ticket_model.Ticket):
        raise NotImplementedError

    @abc.abstractmethod
    def find_by_id(self, ticket_id) -> ticket_model.Ticket:
        raise NotImplementedError


class DynamoDbRepository(AbstractRepository):
    """
    Ticket - Dynamo Item
        PK: TICKET#{ticket_id}          ex. TICKET#ebaf99c01b1a4cda91b7bf34e6db231d
        SK: METADATA#{ticket_id}        ex. METADATA#ebaf99c01b1a4cda91b7bf34e6db231d
        lock_version: 1
        state: "AWAITING_ACCEPTANCE"
        previous_state: "CREATE_PENDING"
        restaurant_id: 1
        line_items: [{
            quantity: 3
            menu_id: "000001",
            name: "Curry Rice",
        }]
        ready_by: "2022-11-30T05:00:30.001000Z"
        accept_by: "2022-11-30T05:00:30.001000Z"
        preparing_time: "2022-11-30T05:00:30.001000Z"
        picked_up_time: "2022-11-30T05:00:30.001000Z"
        ready_for_pickup_time: "2022-11-30T05:00:30.001000Z"
    """

    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'KitchenService')

    def save(self, ticket: ticket_model.Ticket):
        print(f'kitchen_repository.py save(): {ticket}')
        ticket_dynamo_dict = self._ticket_obj_to_dynamo_dict(ticket)

        with dx.dynamo_exception_check():
            resp = self.client.put_item(
                TableName=self.table_name,
                Item=ticket_dynamo_dict
            )
            return resp

    def find_by_id(self, ticket_id) -> ticket_model.Ticket:

        with dx.dynamo_exception_check():
            resp = self.client.get_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'TICKET#{ticket_id}'},
                    'SK': {'S': f'TICKET#{ticket_id}'},
                },
            )

        if not resp.get('Item', None):
            raise ex.ItemNotFoundException(f'ticket_id: {ticket_id}')

        return self._dynamo_obj_to_ticket_python_obj(resp['Item'])

    @staticmethod
    def _ticket_obj_to_dynamo_dict(ticket: ticket_model.Ticket):
        """ Ticket -> DynamoDB obj """
        print(f'kitchen_repository.py _ticket_obj_to_dynamo_dict(): {ticket}')

        # ticketをPython obj(dict)に変換
        ticket_dict = ticket.to_dict()

        # DynamoDB PrimaryKey変換: PK, SKの変更
        ticket_dict['PK'] = f"TICKET#{ticket_dict['ticket_id']}"
        ticket_dict['SK'] = f"TICKET#{ticket_dict['ticket_id']}"
        del ticket_dict['ticket_id']

        # valueがNoneのものを削除する (MAPなどのnest階層はそのまま)
        without_none = {k: v for k, v in ticket_dict.items() if v is not None}
        ticket_dict.clear()
        ticket_dict.update(without_none)

        # Dynamo objに変換
        serializer = boto3.dynamodb.types.TypeSerializer()
        dynamo_dict = {k: serializer.serialize(v) for k, v, in ticket_dict.items()}
        return dynamo_dict

    @staticmethod
    def _dynamo_obj_to_ticket_python_obj(dynamo_item):
        """ DynamoDB obj -> Ticket Obj """
        # Dynamo obj -> Python obj
        print(f'kitchen_repository.py _dynamo_obj_to_ticket_python_obj(): '
              f'{json.dumps(dynamo_item)}')

        deserializer = boto3.dynamodb.types.TypeDeserializer()
        python_obj = {k: deserializer.deserialize(v) for k, v in dynamo_item.items()}
        # Primary Keyの変更: PK, SKをticket attributeに変換
        python_obj['ticket_id'] = python_obj['PK'].split('#')[1]
        del python_obj['PK']
        del python_obj['SK']

        ticket = ticket_model.Ticket.from_dict(python_obj)
        return ticket
