from __future__ import annotations
import datetime
import json
import dataclasses
import decimal
from kitchen_layer.domain import ticket_model
from kitchen_layer.common import common


class DomainEvent:
    pass


# Todo: for Saga
@dataclasses.dataclass
class TicketCreated(DomainEvent):
    event_id: str
    ticket_id: str
    restaurant_id: int
    # line_items: ticket_model.TicketDetails
    line_items: list[ticket_model.TicketLineItem]

    @staticmethod
    def encoder_(o):
        if isinstance(o, TicketCreated):
            return o.__dict__
        # if isinstance(o, ticket_model.TicketDetails):
        #     return o.line_items
        if isinstance(o, ticket_model.TicketLineItem):
            return o.__dict__
        if isinstance(o, decimal.Decimal):  # Todo: Service内のDecimal処理をどうする？
            if int(o) == o:
                return int(o)
            else:
                return float(o)
        raise TypeError(f'{repr(o)} is not serializable')

    def to_dict(self):
        return json.loads(json.dumps(self, default=self.encoder_))


@dataclasses.dataclass
class TicketCancelled(DomainEvent):
    event_id: str
    ticket_id: str

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class TicketAccepted(DomainEvent):
    event_id: str
    ticket_id: str
    ready_by: datetime.datetime

    # Todo: Implement
    # @classmethod
    # def from_json(cls, body_json):
    #     body_dict = json.loads(body_json, parse_float=decimal.Decimal, parse_int=decimal.Decimal)
    #     # Todo: intもfloatもDecimal()にする!!
    #     restaurant = model.Restaurant.from_dict(body_dict)
    #     return cls(restaurant=restaurant)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, TicketAccepted):
                return o.__dict__
            if isinstance(o, datetime.datetime):
                return o.isoformat() + 'Z'
            raise TypeError(f'{repr(o)} is not serializable')
        return json.loads(json.dumps(self, default=encoder_))


# Todo: 使われてないかも
@dataclasses.dataclass
class TicketPreparationStarted(DomainEvent):
    event_id: str
    ticket_id: str

    def to_dict(self):
        return dataclasses.asdict(self)

# Todo: 使われてないかも
@dataclasses.dataclass
class TicketPreparationCompleted(DomainEvent):
    event_id: str
    ticket_id: str

    def to_dict(self):
        return dataclasses.asdict(self)

# Todo: 使われてないかも
@dataclasses.dataclass
class TicketPickedUp(DomainEvent):
    event_id: str
    ticket_id: str

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class TicketRevised(DomainEvent):
    event_id: str
    ticket_id: str

    def to_dict(self):
        return dataclasses.asdict(self)
