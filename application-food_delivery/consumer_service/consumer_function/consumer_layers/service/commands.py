import dataclasses
import json
import decimal
from consumer_layers.common import common


class Command:
    pass


@dataclasses.dataclass
class CreateConsumer(Command):
    name: common.PersonName

    @classmethod
    def from_json(cls, body_json: str):
        d = json.loads(body_json, parse_float=decimal.Decimal)
        d['name'] = common.PersonName.from_dict(d['name'])
        return cls(**d)


@dataclasses.dataclass
class GetConsumer(Command):
    consumer_id: str


@dataclasses.dataclass
class ValidateOrderForConsumer(Command):
    consumer_id: int
    money_total: common.Money

    # @classmethod
    # def from_json(cls, body_json: str):
    #     d = json.loads(body_json, parse_float=decimal.Decimal)
    #     d['money_total'] = common.Money.from_dict(d['money_total'])
    #     return cls(**d)
