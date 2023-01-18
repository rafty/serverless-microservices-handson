"""
Events from Other Service
"""
import dataclasses
import json
import decimal
from order_history_layers.model import order_history_model
from order_history_layers.common import json_encoder


# @dataclasses.dataclass
# class Event:
#     event_id: int       # 追加 for event_envelope
#     timestamp: str      # 追加 for event_envelope


@dataclasses.dataclass
class DomainEventEnvelope:
    aggregate: str  # Order
    aggregate_id: str  # order_id
    event_type: str  # OrderCreated, OrderApproved
    event_id: int  # 1, 2, 3... Sequential
    timestamp: str  # ISO 8601: 2022-11-30T05:00:30.001000Z
    # domain_event: order_domain_events.DomainEvent

    # @classmethod
    # def wrap(cls, event: order_domain_events.DomainEvent):
    #
    #     print(f'event: {event}')
    #
    #     return DomainEventEnvelope(
    #         aggregate='ORDER',
    #         aggregate_id=event.order_id,
    #         event_type=event.__class__.__name__,
    #         event_id=None,  # Repositoryで対応
    #         timestamp=None,  # Repositoryで対応
    #         domain_event=event)


@dataclasses.dataclass
class OrderCreated(DomainEventEnvelope):
    order_id: str
    order_details: order_history_model.OrderDetails
    delivery_information: order_history_model.DeliveryInformation

    @classmethod
    def from_event(cls, event: dict):
        # print(f'OrderCreated.from_event(): {json.dumps(event, cls=json_encoder.JSONEncoder)}')
        """
        {
            "event_id": "43",
            "delivery_information": {
                "delivery_address": {
                    "zip": "94612",
                    "city": "Oakland",
                    "street1": "9 Amazing View",
                    "street2": "Soi 8",
                    "state": "CA"
                },
                "delivery_time": "2022-11-30T05:00:30.001000Z"
            },
            "order_details": {
                "consumer_id": 4,
                "restaurant_id": 27,
                "order_line_items": [
                    {
                        "quantity": 3,
                        "price": {
                            "currency": "JPY",
                            "value": 800
                        },
                        "name": "Curry Rice",
                        "menu_id": "000001"
                    },
                    {
                        "quantity": 2,
                        "price": {
                            "currency": "JPY",
                            "value": 1000
                        },
                        "name": "Hamburger",
                        "menu_id": "000002"
                    },
                    {
                        "quantity": 1,
                        "price": {
                            "currency": "JPY",
                            "value": 700
                        },
                        "name": "Ramen",
                        "menu_id": "000003"
                    }
                ],
                "order_total": {
                    "currency": "JPY",
                    "value": 5100
                }
            },
            "order_id": "1b3d5cc1a8d64c53aba796364af9eab6",
            "timestamp": "2023-01-10T07:53:40.478405Z",
            "aggregate": "ORDER",
            "aggregate_id": "1b3d5cc1a8d64c53aba796364af9eab6",
            "event_type": "OrderCreated"
        }
        """

        event['order_details'] = order_history_model.OrderDetails.from_dict(event['order_details'])
        event['delivery_information'] = order_history_model.DeliveryInformation.from_dict(
                                                                     event['delivery_information'])
        return cls(**event)


@dataclasses.dataclass
class OrderAuthorized(DomainEventEnvelope):
    order_id: str

    @classmethod
    def from_event(cls, event: dict):
        # print(f'OrderAuthorized.from_event(): {json.dumps(event, cls=json_encoder.JSONEncoder)}')
        return cls(**event)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, OrderAuthorized):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_))
        return d


@dataclasses.dataclass
class OrderRejected(DomainEventEnvelope):
    order_id: str

    @classmethod
    def from_event(cls, event: dict):
        # print(f'OrderRejected.from_event(): {json.dumps(event, cls=json_encoder.JSONEncoder)}')
        return cls(**event)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, OrderRejected):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_))
        return d


@dataclasses.dataclass
class OrderCancelled(DomainEventEnvelope):
    order_id: str

    @classmethod
    def from_event(cls, event: dict):
        # print(f'OrderCancelled.from_event(): {json.dumps(event, cls=json_encoder.JSONEncoder)}')
        return cls(**event)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, OrderCancelled):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_))
        return d

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, OrderCancelled):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_))
        return d


@dataclasses.dataclass
class DeliveryPickedup(DomainEventEnvelope):
    delivery_id: str

    @classmethod
    def from_event(cls, event: dict):
        # print(f'DeliveryPickedup.from_event(): {json.dumps(event, cls=json_encoder.JSONEncoder)}')
        return cls(**event)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, DeliveryPickedup):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_))
        return d


@dataclasses.dataclass
class DeliveryDelivered(DomainEventEnvelope):
    delivery_id: str

    @classmethod
    def from_event(cls, event: dict):
        # print(f'DeliveryDelivered.from_event(): {json.dumps(event, cls=json_encoder.JSONEncoder)}')
        return cls(**event)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, DeliveryDelivered):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_))
        return d
