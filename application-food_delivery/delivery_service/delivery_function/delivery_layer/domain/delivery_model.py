from __future__ import annotations  # classの依存関係の許可
import dataclasses
import enum
import decimal
import datetime
import json
from delivery_layer.common import common


class DeliveryState(enum.Enum):
    PENDING = 'PENDING'
    SCHEDULED = 'SCHEDULED'
    CANCELLED = 'CANCELLED'


class Delivery:
    """
    DynamoDB Table Construction
        PK: DELIVERY#{delivery_id}
        SK: DELIVERY#{delivery_id}
        name: {
            'first_name': 'Takashi',
            'last_name': 'Yagita',
        }
    """

    def __init__(self,
                 delivery_id: int,
                 restaurant_id: int,
                 pickup_address: common.Address,
                 delivery_address: common.Address,
                 state: DeliveryState = None,
                 pickup_time=None,
                 delivery_time=None,
                 ready_by=None,
                 assigned_courier=None):

        self.delivery_id = delivery_id
        self.state = state if state else DeliveryState.PENDING
        self.pickup_address = pickup_address
        self.delivery_address = delivery_address
        self.restaurant_id = restaurant_id
        self.pickup_time: datetime.datetime = pickup_time if pickup_time else None
        self.delivery_time: datetime.datetime = delivery_time if delivery_time else None
        self.ready_by: datetime.datetime = ready_by if ready_by else None
        self.assigned_courier: int = assigned_courier if assigned_courier else None

    @classmethod
    def create(cls,
               delivery_id: int,
               restaurant_id: int,
               pickup_address: common.Address,
               delivery_address: common.Address):

        delivery = cls(delivery_id=delivery_id,
                       restaurant_id=restaurant_id,
                       pickup_address=pickup_address,
                       delivery_address=delivery_address)
        return delivery

    @classmethod
    def from_dict(cls, d: dict):
        """
        {
            'delivery_id': 'e17611470da34124a77c5d340b403478',
            'restaurant_id': Decimal('27'),
            'pickup_address': {
                'zip': '94611',
                'street1': '1 Main Street',
                'street2': 'Unit 99',
                'state': 'CA',
                'city': 'Oakland'
            },
            'delivery_address': {
                'zip': '94612',
                'street1': '9 Amazing View',
                'street2': 'Soi 8',
                'state': 'CA',
                'city': 'Oakland'
            },
            'assigned_courier': Decimal('1002'),
            'ready_by': '2022-11-30T05:00:30.001000Z',
            'state': 'SCHEDULED'
        }
        """
        d['pickup_address'] = common.Address.from_dict(d['pickup_address'])
        d['delivery_address'] = common.Address.from_dict(d['delivery_address'])
        if d.get('ready_by', None):
            d['ready_by'] = datetime.datetime.strptime(d['ready_by'], '%Y-%m-%dT%H:%M:%S.%fZ')
        d['state'] = DeliveryState(d['state'])
        return cls(**d)

    @classmethod
    def from_cmd_dict(cls, d: dict):
        """
        {
                'delivery_id': 1,
                'restaurant_id': 1,
                'pickup_address': {
                    "street1": "1 Main Street",
                    "street2": "Unit 99",
                    "city": "Oakland",
                    "state": "CA",
                    "zip": "94611"
                },
                'delivery_address': {
                    "street1": "9 Amazing View",
                    "street2": "Soi 9",
                    "city": "Oakland",
                    "state": "CA",
                    "zip": "94612"
                },
            }
        """
        pickup_address = common.Address.from_dict(d['pickup_address'])
        delivery_address = common.Address.from_dict(d['delivery_address'])
        return cls(delivery_id=d['delivery_id'],
                   restaurant_id=d['restaurant_id'],
                   pickup_address=pickup_address,
                   delivery_address=delivery_address)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, Delivery):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, common.Address):
                return dataclasses.asdict(o)
            if isinstance(o, DeliveryState):  # Enum
                return o.value
            if isinstance(o, datetime.datetime):
                return o.isoformat() + 'Z'
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        dict_ = json.loads(json.dumps(self, default=encoder_), parse_float=decimal.Decimal)
        return dict_

    def schedule(self, ready_by: datetime.datetime, assigned_courier: int) -> Delivery:
        self.ready_by = ready_by
        self.assigned_courier = assigned_courier
        self.state = DeliveryState.SCHEDULED
        return self

    def cancel(self) -> Delivery:
        self.state = DeliveryState.CANCELLED
        self.assigned_courier = None
        return self
