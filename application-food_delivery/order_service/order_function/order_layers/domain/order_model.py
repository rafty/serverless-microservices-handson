from __future__ import annotations  # classの依存関係の許可
import dataclasses
import json
import decimal
import enum
import datetime
import uuid
import typing
from order_layers.common import common
from order_layers.common import exception
from order_layers.domain import restaurant_model
from order_layers.domain import order_domain_events


class OrderState(enum.Enum):
    APPROVAL_PENDING = 'APPROVAL_PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    REVISION_PENDING = 'REVISION_PENDING'
    CANCEL_PENDING = 'CANCEL_PENDING'
    CANCELLED = 'CANCELLED'


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


# ------------------ for order change ---------------------------------
@dataclasses.dataclass(unsafe_hash=True, frozen=True)
class RevisedOrderLineItem:
    quantity: int
    menu_id: str

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclasses.dataclass(unsafe_hash=True, frozen=True)
class OrderRevision:
    delivery_information: typing.Optional[DeliveryInformation]
    revised_order_line_items: list[RevisedOrderLineItem]

    @classmethod
    def from_dict(cls, d):
        delivery_information = DeliveryInformation.from_dict(d['delivery_information'])
        revised_order_line_items = [RevisedOrderLineItem.from_dict(item)
                                    for item in d['revised_order_line_items']]
        return cls(delivery_information=delivery_information,
                   revised_order_line_items=revised_order_line_items)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, OrderRevision):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, DeliveryInformation):
                return o.to_dict()
            if isinstance(o, RevisedOrderLineItem):
                return dataclasses.asdict(o)
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


@dataclasses.dataclass(unsafe_hash=True, frozen=True)
class LineItemQuantityChange:
    # Todo ?: OrderLineItemsのDomain Service?
    # Todo ?: OrderLineItemsの中に入れられないのか？
    current_order_total: common.Money
    new_order_total: common.Money
    delta: common.Money

    def to_dict(self):
        return dataclasses.asdict(self)

# ------------------ for order change ---------------------------------


@dataclasses.dataclass(unsafe_hash=True, frozen=True)
class PaymentInformation:
    pyment_token: str


# for Order Created Event
@dataclasses.dataclass(frozen=True)
class OrderDetails:
    consumer_id: int
    restaurant_id: int
    order_line_items: list[OrderLineItem]
    order_total: common.Money

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

    def delta_for_changed_quantity(self, new_quantity: int) -> common.Money:
        return self.price * (new_quantity - self.quantity)

    def get_total(self):
        sum_ = self.price * self.quantity
        return sum_

    def __eq__(self, other):
        if isinstance(other, OrderLineItem):
            if self.__dict__ == other.__dict__:
                return True
            else:
                return False

    def __hash__(self):
        return hash(self.menu_id) + hash(self.name) + hash(self.price) + hash(self.quantity)


class OrderLineItems:

    def __init__(self, line_items: list[OrderLineItem]) -> None:
        self.line_items: list[OrderLineItem] = line_items

    @classmethod
    def from_dict_list(cls, item_list: list[dict]):
        list_ = [OrderLineItem.from_dict(item) for item in item_list]
        return cls(list_)

    def to_dict_list(self):
        def encoder_(o):
            if isinstance(o, OrderLineItems):
                return o.__dict__  # ここがポイント
            if isinstance(o, OrderLineItem):
                return o.to_dict()  # ここがポイント
            if isinstance(o, common.Money):
                return o.to_dict()
            raise TypeError(f'{repr(o)} is not serializable')

        d_list = [json.loads(json.dumps(item, default=encoder_))
                  for item in self.line_items]
        return d_list

    def order_total(self) -> common.Money:
        money_list = [line_item.get_total() for line_item in self.line_items]
        sum_value = sum(money.value for money in money_list)
        currency = money_list[0].currency
        return common.Money(sum_value, currency)

    def line_item_quantity_change(self, order_revision) -> LineItemQuantityChange:
        """ quantityの変更で変わる金額を算出 """
        current_order_total = self.order_total()
        delta = self.change_to_order_total(order_revision)
        new_order_total = current_order_total + delta
        return LineItemQuantityChange(current_order_total, new_order_total, delta)

    def change_to_order_total(self, order_revision: OrderRevision) -> common.Money:
        price_list = []
        for item in order_revision.revised_order_line_items:
            """
            order_revision.revised_order_line_items: list[RevisedOrderLineItem]
            item:RevisedOrderLineItem
            """
            line_item: OrderLineItem = self.find_order_line_items(item.menu_id)
            price = line_item.delta_for_changed_quantity(item.quantity)
            price_list.append(price)

        # common.Money Listの合計を算出
        sum_value = sum(money.value for money in price_list)
        currency = price_list[0].currency
        line_item_total_price = common.Money(sum_value, currency)
        return line_item_total_price

    def find_order_line_items(self, line_item_id: str):
        for line_item in self.line_items:
            if line_item.menu_id == line_item_id:
                return line_item
        raise exception.LineItemNotFound(f'Line item not found {line_item_id}')

    def update_line_items(self, order_revision: OrderRevision):
        for line_item in self.line_items:
            for item in order_revision.revised_order_line_items:
                if line_item.menu_id == item.menu_id:
                    line_item.quantity = item.quantity

    # def __eq__(self, other):
    #     if isinstance(other, OrderLineItems):
    #         if set(self.line_items) == set(other.line_items):
    #             # Todo: listの比較はsetで行う。
    #             return True
    #         else:
    #             return False


class Order:
    def __init__(self,
                 consumer_id: int,
                 restaurant_id: int,
                 delivery_information: DeliveryInformation,
                 order_line_items: OrderLineItems,
                 order_id=None,
                 lock_version=None,
                 order_state=None,
                 order_minimum=None,
                 ) -> None:

        # Todo: [必須]　ORDER#{id}はdomainでuuidを生成しているが、
        #  　　　　　　　at least onceの重複を避けるためにrequest_idを使用すること。
        #             注文ID(uuid)はクライアント側で生成すること
        self.order_id = order_id if order_id else uuid.uuid4().hex
        self.lock_version = lock_version if lock_version else 1  # for optimistic lock
        self.order_state = order_state if order_state else OrderState.APPROVAL_PENDING
        max_value = 0x7fffffff  # Minimum order amount
        self.order_minimum: common.Money = order_minimum if order_minimum else common.Money(max_value, 'JPY')
        self.consumer_id = consumer_id
        self.restaurant_id = restaurant_id
        self.order_line_items: OrderLineItems = order_line_items
        self.delivery_information: DeliveryInformation = delivery_information
        self.payment_information: PaymentInformation = None  # Not Used

    @classmethod
    def from_dict(cls, d: dict):
        d['delivery_information'] = DeliveryInformation.from_dict(d['delivery_information'])
        d['order_line_items'] = OrderLineItems.from_dict_list(d['order_line_items'])
        d['order_state'] = OrderState(d['order_state'])
        d['order_minimum'] = common.Money.from_dict(d['order_minimum'])
        return cls(**d)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, Order):
                return o.__dict__  # ここがポイント
            if isinstance(o, DeliveryInformation):
                return o.to_dict()  # ここがポイント
            if isinstance(o, OrderLineItems):
                return o.to_dict_list()
            if isinstance(o, OrderState):
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
    def create_order(cls,
                     consumer_id: int,
                     restaurant: restaurant_model.Restaurant,
                     delivery_information: DeliveryInformation,
                     order_line_items: OrderLineItems
                     ) -> (Order, order_domain_events.OrderCreated):

        # ---- for Order Instance ----
        order = Order(consumer_id=consumer_id,
                      restaurant_id=restaurant.restaurant_id,
                      delivery_information=delivery_information,
                      order_line_items=order_line_items)

        # ---- for domain events ----
        order_details = OrderDetails(consumer_id=order.consumer_id,
                                     restaurant_id=order.restaurant_id,
                                     order_line_items=order.order_line_items.line_items,
                                     order_total=order.get_order_total())

        event = order_domain_events.OrderCreated(order_id=order.order_id,
                                                 order_details=order_details,
                                                 delivery_information=delivery_information)

        # Todo: [event]をシングルに変更する。
        #  REST APIでevent_idをシンプルに返せるようにするため。
        #  複数Eventを返したいときはAdditionalEventとして返す。
        # return order, [event]
        return order, event

    def get_order_total(self):
        return self.order_line_items.order_total()

    def note_approved(self):
        if self.order_state == OrderState.APPROVAL_PENDING:
            self.order_state = OrderState.APPROVED

            # Todo: [event]をシングルに変更する。
            # return self, [order_domain_events.OrderAuthorized(order_id=self.order_id)]
            return self, order_domain_events.OrderAuthorized(order_id=self.order_id)
        else:
            raise exception.UnsupportedStateTransitionException(
                f'Unsupported State{self.order_state}')

    def cancel(self):
        if self.order_state == OrderState.APPROVED:
            self.order_state = OrderState.CANCEL_PENDING

            # Todo: [event]をシングルに変更する。
            # return self, []  # 必要なければDomain Eventを発行しない
            return self, None  # 必要なければDomain Eventを発行しない
        else:
            raise exception.UnsupportedStateTransitionException(
                f'Unsupported State {self.order_state}')

    def note_canceled(self) -> (Order, list[order_domain_events.OrderCancelled]):
        if self.order_state == OrderState.CANCEL_PENDING:
            self.order_state = OrderState.CANCELLED

            # Todo: [event]をシングルに変更する。
            # return self, [order_domain_events.OrderCancelled(order_id=self.order_id)]
            return self, order_domain_events.OrderCancelled(order_id=self.order_id)
        else:
            raise exception.UnsupportedStateTransitionException(
                f'Unsupported State {self.order_state}')

    def undo_pending_cancel(self) -> (Order, list):
        if self.order_state == OrderState.CANCEL_PENDING:
            self.order_state = OrderState.APPROVED
            return self, []  # empty domain event
        else:
            raise exception.UnsupportedStateTransitionException(
                f'Unsupported State{self.order_state}')

    def note_rejected(self):
        if self.order_state == OrderState.APPROVAL_PENDING:
            self.order_state = OrderState.REJECTED
            # Todo: [event]をシングルに変更する。
            # return self, [order_domain_events.OrderRejected(order_id=self.order_id)]
            return self, order_domain_events.OrderRejected(order_id=self.order_id)
        else:
            raise exception.UnsupportedStateTransitionException(
                f'Unsupported State{self.order_state}')

    def revise(self, order_revision: OrderRevision) \
            -> (Order, LineItemQuantityChange, order_domain_events.DomainEvent):

        if self.order_state == OrderState.APPROVED:

            # quantityの変更で変わる金額を算出  -> current_order_total, new_order_total, delta
            change: LineItemQuantityChange = \
                self.order_line_items.line_item_quantity_change(order_revision)

            # (注) 不変条件
            # new_order_totalがmin以上かどうか
            if change.new_order_total >= self.order_minimum:
                raise exception.OrderMinimumNotMetException(f'{change.new_order_total}')

            self.order_state = OrderState.REVISION_PENDING

            # Todo: [event]をシングルに変更する。
            # events = [
            #     order_domain_events.OrderRevisionProposed(
            #                                         order_id=self.order_id,
            #                                         order_revision=order_revision,
            #                                         current_order_total=change.current_order_total,
            #                                         new_order_total=change.new_order_total)
            # ]
            # return self, change, events
            event = order_domain_events.OrderRevisionProposed(
                                                    order_id=self.order_id,
                                                    order_revision=order_revision,
                                                    current_order_total=change.current_order_total,
                                                    new_order_total=change.new_order_total)
            return self, change, event
        else:
            raise exception.UnsupportedStateTransitionException(
                f'Unsupported State{self.order_state}')

    def confirm_revision(self, order_revision: OrderRevision) -> \
            (Order, list[order_domain_events.DomainEvent]):

        if self.order_state == OrderState.REVISION_PENDING:
            line_item_quantity_change: LineItemQuantityChange = \
                self.order_line_items.line_item_quantity_change(order_revision)
            if order_revision.delivery_information:
                self.delivery_information = order_revision.delivery_information
            if order_revision.revised_order_line_items is not None \
                    and len(order_revision.revised_order_line_items) > 0:
                self.order_line_items.update_line_items(order_revision)

            self.order_state = OrderState.APPROVED

            # Todo: [event]をシングルに変更する。
            # return self, [order_domain_events.OrderRevised(
            #                      order_id=self.order_id,
            #                      order_revision=order_revision,
            #                      current_order_total=line_item_quantity_change.current_order_total,
            #                      new_order_total=line_item_quantity_change.new_order_total)]
            return self, order_domain_events.OrderRevised(
                                 order_id=self.order_id,
                                 order_revision=order_revision,
                                 current_order_total=line_item_quantity_change.current_order_total,
                                 new_order_total=line_item_quantity_change.new_order_total)
        else:
            raise exception.UnsupportedStateTransitionException(
                f'Unsupported State{self.order_state}')

    def undo_revise_order(self):
        if self.order_state == OrderState.REVISION_PENDING:
            self.order_state = OrderState.APPROVED
            # Todo: [event]をシングルに変更する。
            # return self, []  # empty domain event
            return self, None  # empty domain event
        else:
            raise exception.UnsupportedStateTransitionException(
                f'Unsupported State{self.order_state}')

    # def reject_revision(self) -> list[domain_event.DomainEvent]:
    #     if self.order_state == OrderState.REVISION_PENDING:
    #         self.order_state = OrderState.APPROVED
    #         return []
    #     else:
    #         raise exception.UnsupportedStateTransitionException(
    #             f'Unsupported State{self.order_state}')
    #
