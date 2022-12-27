import dataclasses
import datetime
import json
import decimal
from kitchen_layer.domain import ticket_model


class Command:
    pass


# Create Order Saga
@dataclasses.dataclass
class CreateTicket(Command):
    ticket_id: int  # from order_id
    restaurant_id: int
    # details: ticket_model.TicketDetails
    line_items: list[ticket_model.TicketLineItem]

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j, parse_float=decimal.Decimal)
        d['line_items'] = [ticket_model.TicketLineItem(**item) for item in d['line_items']]
        return cls(**d)


# Create Order Saga - 補償トランザクション
@dataclasses.dataclass
class CancelCreateTicket(Command):
    ticket_id: int

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j, parse_float=decimal.Decimal)
        return cls(**d)


# Create Order Saga
@dataclasses.dataclass
class ConfirmCreateTicket(Command):
    ticket_id: int

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j, parse_float=decimal.Decimal)
        return cls(**d)


# Cancel Order Saga
@dataclasses.dataclass
class BeginCancelTicket(Command):
    ticket_id: int

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j, parse_float=decimal.Decimal)
        return cls(**d)


# Cancel Order Saga
@dataclasses.dataclass
class ConfirmCancelTicket(Command):
    ticket_id: int  # order_idと同じ
    # restaurant_id: int

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j, parse_float=decimal.Decimal)
        return cls(**d)


# Cancel Order Saga
@dataclasses.dataclass
class UndoBeginCancelTicket(Command):
    ticket_id: int  # order_idと同じ
    # restaurant_id: int

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j, parse_float=decimal.Decimal)
        return cls(**d)


# Cancel Order Saga
@dataclasses.dataclass
class BeginCancelTicket(Command):
    ticket_id: int

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j, parse_float=decimal.Decimal)
        return cls(**d)

# ---------------------------------------------------------
# Revise Order Saga
# ---------------------------------------------------------


@dataclasses.dataclass
class BeginReviseTicket(Command):
    ticket_id: int  # order_idと同じ
    revised_order_line_items: ticket_model.RevisedOrderLineItem
    # restaurant_id: int  # Not used. For verify restaurant id.

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j, parse_float=decimal.Decimal)
        return cls(**d)


@dataclasses.dataclass
class ConfirmReviseTicket(Command):
    ticket_id: int  # order_idと同じ
    revised_order_line_items: ticket_model.RevisedOrderLineItem
    # restaurant_id: int  # Not used. For verify restaurant id.

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j, parse_float=decimal.Decimal)
        return cls(**d)


@dataclasses.dataclass
class UndoBeginReviseTicket(Command):
    ticket_id: int  # order_idと同じ
    # restaurant_id: int  # Not used. For verify restaurant id.

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j, parse_float=decimal.Decimal)
        return cls(**d)


# Todo: path="/tickets/{ticketId}/accept" POST
@dataclasses.dataclass
class AcceptTicket(Command):
    ticket_id: int
    ready_by: datetime.datetime

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j, parse_float=decimal.Decimal)
        d['ready_by'] = datetime.datetime.strptime(d['ready_by'], '%Y-%m-%dT%H:%M:%S.%fZ')
        return cls(**d)

