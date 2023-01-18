from __future__ import annotations  # classの依存関係の許可
import dataclasses
import decimal
import datetime
import enum
import json
from delivery_layer.common import common


class DeliveryActionType(enum.Enum):
    PICKUP = 'PICKUP'
    DROPOFF = 'DROPOFF'
    PICKEDUP = 'PICKEDUP'
    DELIVERED = 'DELIVERED'


class Action:
    def __init__(self, action_type: DeliveryActionType, delivery_id, address, time):
        self.action_type: DeliveryActionType = action_type
        self.delivery_id = delivery_id
        self.address: common.Address = address
        self.time: datetime.datetime = time

    def action_for(self, delivery_id) -> bool:
        return self.delivery_id == delivery_id

    @classmethod
    def make_pickup(cls, delivery_id, pickup_address, pickup_time):
        return cls(action_type=DeliveryActionType.PICKUP,
                   delivery_id=delivery_id,
                   address=pickup_address,
                   time=pickup_time)

    @classmethod
    def make_dropoff(cls, delivery_id, delivery_address, delivery_time):
        return cls(action_type=DeliveryActionType.DROPOFF,
                   delivery_id=delivery_id,
                   address=delivery_address,
                   time=delivery_time)

    @classmethod
    def make_pickedup(cls, delivery_id, pickup_address, pickedup_time):
        return cls(action_type=DeliveryActionType.PICKEDUP,
                   delivery_id=delivery_id,
                   address=pickup_address,
                   time=pickedup_time)

    @classmethod
    def make_delivered(cls, delivery_id, delivery_address, delivered_time):
        return cls(action_type=DeliveryActionType.DELIVERED,
                   delivery_id=delivery_id,
                   address=delivery_address,
                   time=delivered_time)

    @classmethod
    def from_dict(cls, d):
        d['action_type'] = DeliveryActionType(d['action_type'])
        d['address'] = common.Address.from_dict(d['address'])
        d['time'] = datetime.datetime.strptime(d['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        return cls(**d)

    def __repr__(self):
        return repr(vars(self))


class Plan:
    def __init__(self):
        self.actions: list[Action] = []

    def add_action(self, action: Action):
        self.actions.append(action)

    def remove_delivery(self, delivery_id):
        # cancelされたdelivery_idに該当するactionを削除する
        self.actions = [action for action in self.actions if action.delivery_id != delivery_id]

    def fetch_assigned_actions(self, delivery_id):
        # sampleではactionsForDelivery()
        # delivery_idに該当するActionを取得
        return [action for action in self.actions if action.delivery_id == delivery_id]

    def __repr__(self):
        return repr(vars(self))

    @classmethod
    def from_dict_list(cls, dl):
        plan = cls()
        plan.actions = [Action.from_dict(action_dict) for action_dict in dl]
        return plan


class Done:
    def __init__(self):
        self.actions: list[Action] = []

    def add_action(self, action: Action):
        self.actions.append(action)

    def fetch_actions(self, delivery_id):
        # sampleではactionsForDelivery()
        # delivery_idに該当するActionを取得
        return [action for action in self.actions if action.delivery_id == delivery_id]

    def __repr__(self):
        return repr(vars(self))

    @classmethod
    def from_dict_list(cls, dl):
        plan = cls()
        plan.actions = [Action.from_dict(action_dict) for action_dict in dl]
        return plan


class Courier:
    """
    DynamoDB Table Construction
        PK: COURIER#{courier_id}
        SK: METADATA#{courier_id}
        available: True/False
        plan: {
            'actions': [
                {
                    'action_type': 'PICKUP',
                    'delivery_id': 'dce6a5874f1c7adf5e7c1f701ed7eb12',
                    'address': {
                        "zip": "94612",
                        "city": "Oakland",
                        "street1": "9 Amazing View",
                        "street2": "Soi 8",
                        "state": "CA"
                    },
                    'time': '2022-11-30T05:00:30.001000Z'
                },
                                {
                    'action_type': 'DROPOFF',
                    'delivery_id': 'dce6a5874f1c7adf5e7c1f701ed7eb12',
                    'address': {
                        "zip": "94612",
                        "city": "Oakland",
                        "street1": "9 Amazing View",
                        "street2": "Soi 8",
                        "state": "CA"
                    },
                    'time': '2022-11-30T05:00:30.001000Z'
                }
            ]
        },
        done: {
            'actions': [
                {
                    'action_type': 'PICKEDUP',
                    'delivery_id': 'dce6a5874f1c7adf5e7c1f701ed7eb12',
                    'address': {
                        "zip": "94612",
                        "city": "Oakland",
                        "street1": "9 Amazing View",
                        "street2": "Soi 8",
                        "state": "CA"
                    },
                    'time': '2022-11-30T05:00:30.001000Z'
                },
                                {
                    'action_type': 'DELIVERED',
                    'delivery_id': 'dce6a5874f1c7adf5e7c1f701ed7eb12',
                    'address': {
                        "zip": "94612",
                        "city": "Oakland",
                        "street1": "9 Amazing View",
                        "street2": "Soi 8",
                        "state": "CA"
                    },
                    'time': '2022-11-30T05:00:30.001000Z'
                }
            ]
        },
    """
    def __init__(self, courier_id: int, available: bool = None, plan: Plan = None, done: Done = None):
        self.courier_id: int = courier_id
        self.available: bool = available if available else None
        self.plan: Plan = plan if plan else Plan()  # 作成時にPlanの空リストが必要。
        self.done: Done = done if done else Done()  # 作成時にPlanの空リストが必要。

    @classmethod
    def create(cls, courier_id: int):
        return cls(courier_id=courier_id)

    def add_action(self, action: Action):
        self.plan.add_action(action)

    def action_for_delivery(self, delivery_id):
        # get_actions()という意味
        # courierに割り当てられたactionを取得する。
        return self.plan.fetch_assigned_actions(delivery_id)

    def cancel_delivery(self, delivery_id) -> Courier:
        self.plan.remove_delivery(delivery_id=delivery_id)
        return self

    def note_available(self):
        self.available = True
        return self

    def note_unavailable(self):
        self.available = False
        return self

    def is_available(self):
        return self.available

    # --------------------------------
    # 新規追加 for Done
    def add_done_action(self, action: Action):
        self.done.add_action(action)

    def fetch_done_actions(self, delivery_id):
        # get_actions()という意味
        # courierに割り当てられたactionを取得する。
        return self.done.fetch_actions(delivery_id)

    @classmethod
    def from_dict(cls, d: dict):
        # from DynamoDB dict
        """
        {
            'courier_id': 1,
            'available': True,
            'plan': [
                {
                    'action_type': 'PICKUP',
                    'delivery_id': 1,
                    'address': {
                        'street1': '1 Main Street',
                        'street2': 'Unit 99',
                        'city': 'Oakland',
                        'state': 'CA',
                        'zip': '94611'
                    },
                    'time': '2022-11-30T05:00:30.001000Z'
                },
            ],
            'done': [
                {
                    'action_type': 'PICKEDUP',
                    'delivery_id': 1,
                    'address': {
                        'street1': '1 Main Street',
                        'street2': 'Unit 99',
                        'city': 'Oakland',
                        'state': 'CA',
                        'zip': '94611'
                    },
                    'time': '2022-11-30T05:00:30.001000Z'
                },
            ]
        }
        """
        d['plan'] = Plan.from_dict_list(d['plan']) if d.get('plan', None) else None
        d['done'] = Done.from_dict_list(d['done']) if d.get('done', None) else None
        return cls(**d)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, Courier):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, Plan):
                return o.actions
            if isinstance(o, Done):
                return o.actions
            if isinstance(o, Action):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, DeliveryActionType):
                return o.value
            if isinstance(o, common.Address):
                return dataclasses.asdict(o)
            if isinstance(o, datetime.datetime):
                return o.isoformat() + 'Z'
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        return json.loads(json.dumps(self, default=encoder_), parse_float=decimal.Decimal)
