import dataclasses
import datetime
from delivery_layer.common import common
from delivery_layer.domain import ticket_model


@dataclasses.dataclass
class Event:
    event_id: int       # 追加 for event_envelope
    timestamp: str      # 追加 for event_envelope


@dataclasses.dataclass
class OrderCreated(Event):
    order_id: int
    delivery_address: common.Address
    restaurant_id: int

    @classmethod
    def from_event(cls, event: dict):
        d = dict()

        d['event_id'] = event['event_id']       # 追加 for event_envelope
        d['timestamp'] = event['timestamp']     # 追加 for event_envelope

        d['order_id'] = event['order_id']
        d['delivery_address'] = event['delivery_information']['delivery_address']
        d['restaurant_id'] = event['order_details']['restaurant_id']
        return cls(**d)


@dataclasses.dataclass
class TicketCreated(Event):
    ticket_id: str
    restaurant_id: int
    line_items: [ticket_model.TicketLineItem]

    @classmethod
    def from_event(cls, event: dict):
        d = dict()
        d['event_id'] = event['event_id']       # 追加 for event_envelope
        d['timestamp'] = event['timestamp']     # 追加 for event_envelope

        d['ticket_id'] = event['ticket_id']
        d['restaurant_id'] = event['restaurant_id']
        d['line_items'] = [ticket_model.TicketLineItem.from_dict(item)
                           for item in event['line_items']]
        return cls(**d)


@dataclasses.dataclass
class TicketAccepted(Event):
    ticket_id: str
    ready_by: datetime.datetime

    @classmethod
    def from_event(cls, event: dict):
        d = dict()
        d['event_id'] = event['event_id']       # 追加 for event_envelope
        d['timestamp'] = event['timestamp']     # 追加 for event_envelope

        d['ticket_id'] = event['ticket_id']
        d['ready_by'] = datetime.datetime.strptime(event['ready_by'], '%Y-%m-%dT%H:%M:%S.%fZ')
        return cls(**d)


@dataclasses.dataclass
class TicketCancelled(Event):
    ticket_id: str

    @classmethod
    def from_event(cls, event: dict):
        d = dict()

        d['event_id'] = event['event_id']       # 追加 for event_envelope
        d['timestamp'] = event['timestamp']     # 追加 for event_envelope

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
        d['event_id'] = event['event_id']       # 追加 for event_envelope
        d['timestamp'] = event['timestamp']     # 追加 for event_envelope

        d['restaurant_id'] = event['restaurant_id']
        d['restaurant_name'] = event['restaurant_name']
        d['restaurant_address'] = common.Address.from_dict(event['restaurant_address'])
        return cls(**d)
