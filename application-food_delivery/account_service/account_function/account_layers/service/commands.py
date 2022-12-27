import dataclasses
import json
import decimal
from account_layers.common import common


class Command:
    pass


@dataclasses.dataclass
class CreateAccount(Command):
    consumer_id: int
    card_information: common.CardInformation

    @classmethod
    def from_json(cls, body_json: str):
        d = json.loads(body_json, parse_float=decimal.Decimal)
        d['card_information'] = common.CardInformation.from_dict(d['card_information'])
        return cls(**d)


@dataclasses.dataclass
class GetAccount(Command):
    # account_id: str
    consumer_id: int


@dataclasses.dataclass
class AuthorizeCard(Command):
    consumer_id: int
    money_total: common.Money

    @classmethod
    def from_json(cls, body_json: str):
        d = json.loads(body_json, parse_float=decimal.Decimal)
        d['money_total'] = common.Money.from_dict(d['money_total'])
        return cls(**d)


@dataclasses.dataclass
class ReverseAuthorizeCard(Command):
    consumer_id: int
    order_id: str
    money_total: common.Money

    @classmethod
    def from_json(cls, body_json: str):
        d = json.loads(body_json, parse_float=decimal.Decimal)
        d['money_total'] = common.Money.from_dict(d['money_total'])
        return cls(**d)


@dataclasses.dataclass
class ReviseAuthorizeCard(Command):
    consumer_id: int
    order_id: str
    money_total: common.Money

    @classmethod
    def from_json(cls, body_json: str):
        d = json.loads(body_json, parse_float=decimal.Decimal)
        d['money_total'] = common.Money.from_dict(d['money_total'])
        return cls(**d)
