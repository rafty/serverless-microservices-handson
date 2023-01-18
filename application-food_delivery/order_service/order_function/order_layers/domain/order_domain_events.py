from __future__ import annotations
import datetime
import json
import dataclasses
import decimal
from order_layers.common import common
from order_layers.domain import order_model


@dataclasses.dataclass
class DomainEvent:
    order_id: str


@dataclasses.dataclass
class OrderCreated(DomainEvent):
    order_details: order_model.OrderDetails
    delivery_information: order_model.DeliveryInformation

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, OrderCreated):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, order_model.OrderDetails):
                return o.to_dict()
            if isinstance(o, order_model.DeliveryInformation):
                return o.to_dict()
            if isinstance(o, common.Address):
                return dataclasses.asdict(o)
            if isinstance(o, datetime.datetime):
                return o.isoformat() + 'Z'
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_))
        return d


# ---------------------------------------------------------
# Create Order Sagaで OrderApprovedになった時に発行されるEvent
# ---------------------------------------------------------
@dataclasses.dataclass
class OrderAuthorized(DomainEvent):
    pass

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class OrderRejected(DomainEvent):
    pass

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class CancelOrderSagaRequested(DomainEvent):
    consumer_id: int
    order_total: common.Money

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class OrderCancelled(DomainEvent):
    pass

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ReviseOrderSagaRequested(DomainEvent):
    consumer_id: int
    order_revision: order_model.OrderRevision

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, ReviseOrderSagaRequested):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, order_model.OrderRevision):
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
class OrderRevised(DomainEvent):
    order_revision: order_model.OrderRevision
    current_order_total: common.Money
    new_order_total: common.Money

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, OrderRevised):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, order_model.OrderRevision):
                return o.to_dict()
            if isinstance(o, order_model.DeliveryInformation):
                return o.to_dict()
            if isinstance(o, common.Address):
                return dataclasses.asdict(o)
            if isinstance(o, common.Money):
                return dataclasses.asdict(o)
            if isinstance(o, datetime.datetime):
                return o.isoformat() + 'Z'
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_))
        return d


@dataclasses.dataclass
class OrderRevisionProposed(DomainEvent):
    order_revision: order_model.OrderRevision
    current_order_total: common.Money
    new_order_total: common.Money

    def to_dict(self):
        # return dataclasses.asdict(self)
        def encoder_(o):
            if isinstance(o, OrderRevisionProposed):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, order_model.OrderRevision):
                return o.to_dict()
            if isinstance(o, order_model.DeliveryInformation):
                return o.to_dict()
            if isinstance(o, order_model.RevisedOrderLineItem):
                return dataclasses.asdict(o)
            if isinstance(o, common.Address):
                return dataclasses.asdict(o)
            if isinstance(o, common.Money):
                return dataclasses.asdict(o)
            if isinstance(o, datetime.datetime):
                return o.isoformat() + 'Z'
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_))
        return d
