from __future__ import annotations  # classの依存関係の許可
import dataclasses
import json
import decimal
import enum
import datetime
from order_history_layers.common import common


class OrderState(enum.Enum):
    APPROVAL_PENDING = 'APPROVAL_PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    REVISION_PENDING = 'REVISION_PENDING'
    CANCEL_PENDING = 'CANCEL_PENDING'
    CANCELLED = 'CANCELLED'


class DeliveryState(enum.Enum):
    PICKEDUP = 'PICKEDUP'
    DELIVERED = 'DELIVERED'


@dataclasses.dataclass(unsafe_hash=True, frozen=True)
class DeliveryInformation:
    delivery_time: datetime.datetime
    delivery_address: common.Address

    @classmethod
    def from_dict(cls, d):
        d['delivery_time'] = \
            datetime.datetime.strptime(d['delivery_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        d['delivery_address'] = common.Address.from_dict(d['delivery_address'])
        return cls(**d)

    def to_dict(self):
        d = dataclasses.asdict(self)
        d['delivery_time'] = datetime.datetime.strftime(d['delivery_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        return d


# for Order Created Event
@dataclasses.dataclass(frozen=True)
class OrderDetails:
    consumer_id: int
    restaurant_id: int
    order_line_items: list[OrderLineItem]
    order_total: common.Money

    @classmethod
    def from_dict(cls, d: dict):
        d['order_line_items'] = [OrderLineItem.from_dict(item) for item in d['order_line_items']]
        d['order_total'] = common.Money.from_dict(d['order_total'])
        return cls(**d)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, OrderDetails):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, OrderLineItem):
                return o.to_dict()
            if isinstance(o, common.Address):
                return o.to_dict()
            if isinstance(o, common.Money):
                return o.to_dict()
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_))
        return d


@dataclasses.dataclass
class OrderLineItem:

    def __init__(self, menu_id: str, name: str, price: common.Money, quantity: int) -> None:
        self.menu_id: str = menu_id
        self.name: str = name
        self.price: common.Money = price
        self.quantity: int = quantity

    @classmethod
    def from_dict(cls, d):
        d['price'] = common.Money.from_dict(d['price'])
        return cls(**d)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, OrderLineItem):
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

    # def delta_for_changed_quantity(self, new_quantity: int) -> common.Money:
    #     return self.price * (new_quantity - self.quantity)
    #
    # def get_total(self):
    #     sum_ = self.price * self.quantity
    #     return sum_
    #
    # def __eq__(self, other):
    #     if isinstance(other, OrderLineItem):
    #         if self.__dict__ == other.__dict__:
    #             return True
    #         else:
    #             return False
    #
    # def __hash__(self):
    #     return hash(self.menu_id) + hash(self.name) + hash(self.price) + hash(self.quantity)


class Order:
    def __init__(self,
                 order_id: str,
                 consumer_id: int,
                 restaurant_id: int,
                 order_state: OrderState,
                 order_line_items: list[OrderLineItem],
                 delivery_information: DeliveryInformation,
                 delivery_state: DeliveryState = None,
                 ) -> None:

        self.order_id = order_id
        self.consumer_id = consumer_id
        self.restaurant_id = restaurant_id
        self.order_state = order_state
        self.order_line_items = order_line_items
        self.delivery_information: DeliveryInformation = delivery_information
        self.delivery_state = delivery_state

    @classmethod
    def create_order(cls,
                     order_id: str,
                     order_details: OrderDetails,
                     delivery_information: DeliveryInformation) -> Order:

        print(f'create_order() order_id: {order_id}')
        print(f'create_order() order_details: {order_details}')
        print(f'create_order() delivery_information: {delivery_information}')

        order = Order(order_id=order_id,
                      consumer_id=order_details.consumer_id,
                      restaurant_id=order_details.restaurant_id,
                      order_state=OrderState.APPROVAL_PENDING,  # Todo: 固定????
                      delivery_information=delivery_information,
                      order_line_items=order_details.order_line_items,
                      delivery_state=None)

        return order

    def to_dict(self):
        # for DynamoDB
        def encoder_(o):
            if isinstance(o, Order):
                return o.__dict__
            if isinstance(o, DeliveryInformation):
                return o.to_dict()  # ここがポイント
            if isinstance(o, OrderLineItem):
                return o.to_dict()
            if isinstance(o, OrderState):
                return o.value
            if isinstance(o, DeliveryState):
                return o.value
            if isinstance(o, common.Money):
                return o.to_dict()
            if isinstance(o, datetime.datetime):
                return o.isoformat() + 'Z'
            if isinstance(o, common.Address):
                return o.to_dict()
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        return json.loads(json.dumps(self, default=encoder_))

    @classmethod
    def from_dict(cls, d: dict):
        # for DynamoDB
        d['delivery_information'] = DeliveryInformation.from_dict(d['delivery_information'])
        d['order_line_items'] = [OrderLineItem.from_dict(item) for item in d['order_line_items']]
        d['order_state'] = OrderState(d['order_state'])
        d['delivery_state'] = DeliveryState(d['delivery_state'])
        return cls(**d)
