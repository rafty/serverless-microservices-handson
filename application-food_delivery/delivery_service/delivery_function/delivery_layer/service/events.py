import dataclasses
import datetime
import json
import decimal
from delivery_layer.common import common


class Event:
    pass


@dataclasses.dataclass
class OrderCreated(Event):
    order_id: int
    delivery_address: common.Address
    restaurant_id: int

    @classmethod
    def from_event(cls, event: dict):
        d = dict()
        d['order_id'] = event['order_id']
        d['delivery_address'] = event['delivery_information']['delivery_address']
        d['restaurant_id'] = event['order_details']['restaurant_id']
        return cls(**d)


@dataclasses.dataclass
class TicketAccepted(Event):
    ticket_id: str
    ready_by: datetime.datetime

    @classmethod
    def from_event(cls, event: dict):
        d = dict()
        d['ticket_id'] = event['ticket_id']
        d['ready_by'] = datetime.datetime.strptime(event['ready_by'], '%Y-%m-%dT%H:%M:%S.%fZ')
        return cls(**d)


@dataclasses.dataclass
class TicketCancelled(Event):
    ticket_id: str

    @classmethod
    def from_event(cls, event: dict):
        d = dict()
        d['ticket_id'] = event['ticket_id']
        return cls(**d)


@dataclasses.dataclass
class RestaurantCreated(Event):
    restaurant_id: int
    restaurant_name: str
    restaurant_address: common.Address

    @classmethod
    def from_event(cls, event: dict):
        d = dict()
        d['restaurant_id'] = event['restaurant_id']
        d['restaurant_name'] = event['restaurant_name']
        d['restaurant_address'] = common.Address.from_dict(event['restaurant_address'])
        return cls(**d)
