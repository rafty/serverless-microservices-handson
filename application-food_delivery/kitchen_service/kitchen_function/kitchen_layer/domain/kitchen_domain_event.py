from __future__ import annotations
import datetime
import json
import dataclasses
import decimal
from kitchen_layer.domain import ticket_model


@dataclasses.dataclass
class DomainEvent:
    ticket_id: str


# Todo: for Saga
@dataclasses.dataclass
class TicketCreated(DomainEvent):
    restaurant_id: int
    line_items: list[ticket_model.TicketLineItem]

    @staticmethod
    def encoder_(o):
        if isinstance(o, TicketCreated):
            return o.__dict__
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
    pass

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class TicketAccepted(DomainEvent):
    ready_by: datetime.datetime

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
    pass

    def to_dict(self):
        return dataclasses.asdict(self)


# Todo: 使われてないかも
@dataclasses.dataclass
class TicketPreparationCompleted(DomainEvent):
    pass

    def to_dict(self):
        return dataclasses.asdict(self)


# Todo: 使われてないかも
@dataclasses.dataclass
class TicketPickedUp(DomainEvent):
    pass

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class TicketRevised(DomainEvent):
    pass

    def to_dict(self):
        return dataclasses.asdict(self)
