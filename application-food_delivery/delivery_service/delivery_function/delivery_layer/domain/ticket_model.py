from __future__ import annotations
import dataclasses
import datetime
import enum
import json
import decimal
from delivery_layer.common import common


class TicketState(enum.Enum):
    CREATE_PENDING = 'CREATE_PENDING'            # <- 1. ticket_create
    AWAITING_ACCEPTANCE = 'AWAITING_ACCEPTANCE'  # <- 2. confirm_create
    ACCEPTED = 'ACCEPTED'                        # <- 3. accept
    PREPARING = 'PREPARING'                      # <- 4. preparing           # Todo: 使われてないかもしれない
    READY_FOR_PICKUP = 'READY_FOR_PICKUP'        # <- 5. ready_for_pickup    # Todo: 使われてないかもしれない
    PICKED_UP = 'PICKED_UP'                      # <- 6. picked_up           # Todo: 使われてないかもしれない
    CANCEL_PENDING = 'CANCEL_PENDING'            # 異常系 cancel <- AWAITING_ACCEPTANCE or ACCEPTED
    CANCELLED = 'CANCELLED'                      # 異常系 confirm_cancel <- CANCEL_PENDING
    REVISION_PENDING = 'REVISION_PENDING'
    # <- begin_revise_order <- AWAITING_ACCEPTANCE or ACCEPTED


# Value Object
@dataclasses.dataclass(frozen=True)
class TicketLineItem:
    quantity: int
    menu_id: str  # javaでは'menuitem_id'
    name: str

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, TicketLineItem):
                return o.__dict__  # ここがポイント
            if isinstance(o, common.Money):
                return o.to_dict()
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')
        return json.loads(json.dumps(self, default=encoder_))


class Ticket:

    def __init__(self,
                 ticket_id: int,  # Todo: intでなくstrでは？
                 restaurant_id: int,
                 line_items: list[TicketLineItem],
                 lock_version=None,
                 state=None,
                 previous_state=None,
                 ready_by=None,
                 accept_time=None,
                 preparing_time=None,
                 picked_up_time=None,
                 ready_for_pickup_time=None):

        self.ticket_id: int = ticket_id  # from order_id  # Todo: intでなくstrでは？
        self.lock_version = lock_version if lock_version else 1  # for optimistic lock
        self.restaurant_id: int = restaurant_id
        self.line_items: list[TicketLineItem] = line_items
        self.state: TicketState = TicketState.CREATE_PENDING if state is None else state
        self.previous_state: TicketState = previous_state if previous_state else None
        self.ready_by: datetime.datetime = ready_by if previous_state else None
        self.accept_time: datetime.datetime = accept_time if accept_time else None
        self.preparing_time: datetime.datetime = preparing_time if preparing_time else None
        self.picked_up_time: datetime.datetime = picked_up_time if picked_up_time else None
        self.ready_for_pickup_time: datetime.datetime = ready_for_pickup_time \
            if ready_for_pickup_time else None

    @classmethod
    def from_dict(cls, d):
        d['line_items'] = [TicketLineItem.from_dict(item) for item in d['line_items']
                           if d.get('line_items', None)]
        d['state'] = TicketState(d['state']) if d.get('state', None) else None
        d['previous_state'] = \
            TicketState(d['previous_state']) if d.get('previous_state', None) else None
        d['ready_by'] = \
            datetime.datetime.strptime(d['ready_by'], '%Y-%m-%dT%H:%M:%S.%fZ') \
            if d.get('ready_by', None) else None
        d['accept_time'] = \
            datetime.datetime.strptime(d['accept_time'], '%Y-%m-%dT%H:%M:%S.%fZ') \
            if d.get('accept_time', None) else None
        d['preparing_time'] = \
            datetime.datetime.strptime(d['preparing_time'], '%Y-%m-%dT%H:%M:%S.%fZ') \
            if d.get('preparing_time', None) else None
        d['picked_up_time'] = \
            datetime.datetime.strptime(d['picked_up_time'], '%Y-%m-%dT%H:%M:%S.%fZ') \
            if d.get('picked_up_time', None) else None
        d['ready_for_pickup_time'] = \
            datetime.datetime.strptime(d['ready_for_pickup_time'], '%Y-%m-%dT%H:%M:%S.%fZ') \
            if d.get('ready_for_pickup_time', None) else None
        return cls(**d)


    def to_dict(self):
        def encoder_(o):
            if isinstance(o, Ticket):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, TicketLineItem):
                # return o.__dict__
                return o.to_dict()
            if isinstance(o, TicketState):
                return o.value
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            if isinstance(o, datetime.datetime):
                return o.isoformat() + 'Z'
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_), parse_float=decimal.Decimal)
        return d
