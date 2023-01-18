import dataclasses
import datetime
import json
import decimal
from delivery_layer.common import common


class Command:
    pass


@dataclasses.dataclass
class CourierAvailability(Command):
    courier_id: int
    available: bool


# java sampleに無い
@dataclasses.dataclass
class CourierPickedUp(Command):
    courier_id: int
    delivery_id: str


# java sampleに無い
@dataclasses.dataclass
class CourierDelivered(Command):
    courier_id: int
    delivery_id: str


# @dataclasses.dataclass
# class CreateDelivery(Command):
#     order_id: int
#     restaurant_id: int
#     pickup_address: common.Address
#     delivery_address: common.Address
#
#     @classmethod
#     def from_json(cls, j: str):
#         d = json.loads(j, parse_float=decimal.Decimal, parse_int=decimal.Decimal)
#         d['delivery_address'] = common.Address.from_dict(d.get('delivery_address'))
#         return cls(**d)


# @dataclasses.dataclass
# class ScheduleDelivery(Command):
#     order_id: int
#     ready_by: datetime.datetime
#
#     @classmethod
#     def from_json(cls, j: str):
#         d = json.loads(j, parse_float=decimal.Decimal, parse_int=decimal.Decimal)
#         d['ready_by'] = datetime.datetime.strptime(d['ready_by'], '%Y-%m-%dT%H:%M:%S.%fZ')
#         return cls(**d)
#


