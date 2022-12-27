import json
import dataclasses
import decimal
from datetime import datetime
from order_layers.common import common
from order_layers.domain import order_model


class Command:
    pass


@dataclasses.dataclass
class OrderRequestLineItems:
    menu_id: str
    quantity: int

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclasses.dataclass
class CreateOrder(Command):
    consumer_id: int
    restaurant_id: int
    order_line_items: list[OrderRequestLineItems]
    delivery_information: order_model.DeliveryInformation

    @classmethod
    def from_json(cls, body_json):
        """{
            "consumer_id": 1511300065921,
            "restaurant_id": 1,
            "delivery_information": {
               "delivery_time": "2022-11-30T05:00:30.001000Z",
               "delivery_address": {
                    "street1": "9 Amazing View",
                    "street2": "Soi 8",
                    "city": "Oakland",
                    "state": "CA",
                    "zip": "94612"
                }
            },
            "order_line_items": [
                {
                    "menu_id": "000001",
                    "quantity": 3
                },
                {
                    "menu_id": "000002",
                    "quantity": 2
                },
                {
                    "menu_id": "000003",
                    "quantity": 1
                }
            ]
        }"""

        d = json.loads(body_json, parse_float=decimal.Decimal)
        d['order_line_items'] = [OrderRequestLineItems.from_dict(item)
                                 for item in d['order_line_items']]

        d['delivery_information'] = order_model.DeliveryInformation.from_dict(d['delivery_information'])
        return cls(**d)


@dataclasses.dataclass
class GetOrder(Command):
    order_id: str


# CreateOrder SAGA Command
@dataclasses.dataclass
class ApproveOrder(Command):
    order_id: str


@dataclasses.dataclass
class RejectOrder(Command):
    order_id: str


@dataclasses.dataclass
class BeginCancelOrder(Command):
    order_id: str


@dataclasses.dataclass
class CancelOrder(Command):
    order_id: str


@dataclasses.dataclass
class ConfirmCancelOrder(Command):
    order_id: str


@dataclasses.dataclass
class UndoBeginCancelOrder(Command):
    order_id: str


@dataclasses.dataclass
class CancelOrder(Command):
    order_id: str


@dataclasses.dataclass
class ReviseOrder(Command):
    order_id: str
    order_revision: order_model.OrderRevision


@dataclasses.dataclass
class BeginReviseOrder(Command):
    order_id: str
    order_revision: order_model.OrderRevision


@dataclasses.dataclass
class ConfirmReviseOrder(Command):
    order_id: str
    order_revision: order_model.OrderRevision


@dataclasses.dataclass
class UndoBeginReviseOrder(Command):
    order_id: str
