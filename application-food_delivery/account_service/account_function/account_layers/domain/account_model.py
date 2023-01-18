from __future__ import annotations
import dataclasses
import decimal
import uuid
import json
import datetime
from account_layers.common import common
from account_layers.domain import domain_events


class Account:
    """
    DynamoDB Table Construction
        PK: CONSUMER#{consumer_id}
        SK: ACCOUNT#{account_id}
    """

    def __init__(self,
                 consumer_id: int,
                 card_information: common.CardInformation,
                 account_id: int = None):

        self.consumer_id: int = consumer_id
        self.card_information: common.CardInformation = card_information
        self.account_id: int = account_id if account_id else uuid.uuid4().hex

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, Account):
                return o.__dict__
            if isinstance(o, common.CardInformation):
                return o.to_dict()
            if isinstance(o, datetime.datetime):
                return o.isoformat() + 'Z'
            if isinstance(o, decimal.Decimal):
                return o  # Decimalのまま返す
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_), parse_float=decimal.Decimal)
        return d

    @classmethod
    def create(cls, consumer_id: int, card_information: common.CardInformation):
        account = cls(consumer_id=consumer_id, card_information=card_information)
        event = domain_events.AccountCreated(consumer_id=account.consumer_id,
                                             account_id=account.account_id)
        return account, event

    def authorize_card(self, order_total: common.Money):
        # Todo: implement some business logic

        # Todo: とりあえず固定でエラーを返していたのできちんとロジックを実装すること。
        # raise exceptions.CardAuthorizationFailedException(
        #     f'CardAuthorizationFailed: consumer_id: {self.consumer_id}')
        return True

    def reverse_authorize_card(self, consumer_id: int, order_id: str, money_total: common.Money):
        # Todo: implement some business logic

        # Todo: とりあえず固定でエラーを返していたのできちんとロジックを実装すること。
        # raise exceptions.CardAuthorizationFailedException(
        #     f'CardAuthorizationFailed: consumer_id: {self.consumer_id}')
        return True

    def revise_authorize_card(self, consumer_id: int, order_id: str, money_total: common.Money):
        print(f' account_model.revise_authorize_card()')

        # Todo: implement some business logic

        # Todo: とりあえず固定でエラーを返していたのできちんとロジックを実装すること。
        # raise exceptions.CardAuthorizationFailedException(
        #     f'CardAuthorizationFailed: consumer_id: {self.consumer_id}')
        return True
