from __future__ import annotations
import dataclasses
import datetime
import enum
import json
import decimal
import uuid
from kitchen_layer.domain import kitchen_domain_event
from kitchen_layer.common import exceptions
from kitchen_layer.common import common


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


# ---------------------------------------------------------------
# Todo:
#       RevisedOrderLineItemはOrderServiceのDomain-ValueObject
#       Ticket Domainに入れるかどうかよく検討すること。
# ----------------------------------------------------------------
@dataclasses.dataclass(unsafe_hash=True, frozen=True)
class RevisedOrderLineItem:
    menu_id: str
    quantity: int


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


# @dataclasses.dataclass(frozen=True)
# class TicketDetails:
#     # Todo: cmdで受け取るときにだけ使うclassで、Ticketが所有するclassではない
#     line_items: list[TicketLineItem]
#
#     @classmethod
#     def from_dict_list(cls, d_list):
#         line_items = [TicketLineItem(**item) for item in d_list]
#         return cls(line_items=line_items)


# Aggregate root - Entity
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

    # @classmethod
    # def create_from_dict(cls, d):
    #     line_items = [TicketLineItem(**item) for item in d['line_items']]
    #     return cls(ticket_id=d['ticket_id'],
    #                restaurant_id=d['restaurant_id'],
    #                line_items=line_items)

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
    # @classmethod
    # def from_dict(cls, d):
    #     line_items = [TicketLineItem(**item)
    #                   for item in d['line_items'] if d.get('line_items', None)]
    #     state = TicketState(d['state']) if d.get('state', None) else None
    #     previous_state = \
    #         TicketState(d['previous_state']) if d.get('previous_state', None) else None
    #     ready_by = datetime.datetime.strptime(d['ready_by'], '%Y-%m-%dT%H:%M:%S.%fZ') \
    #         if d.get('ready_by', None) else None
    #     accept_time = datetime.datetime.strptime(d['accept_time'], '%Y-%m-%dT%H:%M:%S.%fZ') \
    #         if d.get('accept_time', None) else None
    #     preparing_time = datetime.datetime.strptime(d['preparing_time'], '%Y-%m-%dT%H:%M:%S.%fZ') \
    #         if d.get('preparing_time', None) else None
    #     picked_up_time = datetime.datetime.strptime(d['picked_up_time'], '%Y-%m-%dT%H:%M:%S.%fZ') \
    #         if d.get('picked_up_time', None) else None
    #     ready_for_pickup_time = \
    #         datetime.datetime.strptime(
    #             d['ready_for_pickup_time'], '%Y-%m-%dT%H:%M:%S.%fZ') if d.get(
    #                                                     'ready_for_pickup_time', None) else None
    #     return cls(ticket_id=d['ticket_id'],
    #                restaurant_id=d['restaurant_id'],
    #                line_items=line_items,
    #                state=state,
    #                previous_state=previous_state,
    #                ready_by=ready_by,
    #                accept_time=accept_time,
    #                preparing_time=preparing_time,
    #                picked_up_time=picked_up_time,
    #                ready_for_pickup_time=ready_for_pickup_time)

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

    @classmethod
    def create_ticket(cls,
                      ticket_id,
                      restaurant_id,
                      line_items) -> (Ticket, kitchen_domain_event.DomainEvent):

        print(f'ticket_model.py create_ticket: {ticket_id}')

        return cls(ticket_id, restaurant_id, line_items), None

    def cancel_create(self):

        if self.state == TicketState.CREATE_PENDING:
            self.state = TicketState.CANCELLED
            return self, kitchen_domain_event.TicketCancelled(ticket_id=self.ticket_id)
        else:
            raise exceptions.UnsupportedStateTransitionException(f'Unsupported State{self.state}')

    def confirm_create(self) -> (Ticket, kitchen_domain_event.TicketCreated):
        if self.state == TicketState.CREATE_PENDING:
            self.state = TicketState.AWAITING_ACCEPTANCE
            return self, kitchen_domain_event.TicketCreated(ticket_id=self.ticket_id,
                                                            restaurant_id=self.restaurant_id,
                                                            line_items=self.line_items)
        else:
            raise exceptions.UnsupportedStateTransitionException(f'Unsupported State{self.state}')

    def cancel(self) -> (Ticket, list):
        if self.state == TicketState.AWAITING_ACCEPTANCE or self.state == TicketState.ACCEPTED:
            self.previous_state = self.state
            self.state = TicketState.CANCEL_PENDING
            return self, []  # return empty domain event list
        else:
            raise exceptions.UnsupportedStateTransitionException(f'Unsupported State{self.state}')

    def confirm_cancel(self) -> (Ticket, kitchen_domain_event.TicketCancelled):
        if self.state == TicketState.CANCEL_PENDING:
            self.state = TicketState.CANCELLED
            return self, kitchen_domain_event.TicketCancelled(ticket_id=self.ticket_id)
        else:
            raise exceptions.UnsupportedStateTransitionException(f'Unsupported State{self.state}')

    def undo_cancel(self) -> (Ticket, kitchen_domain_event.TicketCancelled):
        if self.state == TicketState.CANCEL_PENDING:
            self.state = self.previous_state
            return self, None  # return empty list
        else:
            raise exceptions.UnsupportedStateTransitionException(f'Unsupported State{self.state}')

    def begin_revise_ticket(self, revise_order_line_items: list[RevisedOrderLineItem]) -> \
            (Ticket, list):

        if self.state == TicketState.AWAITING_ACCEPTANCE or self.state == TicketState.ACCEPTED:
            self.previous_state = self.state
            self.state = TicketState.REVISION_PENDING
            # RevisedOrderLineItem処理は行わない。実際にReviseがConfirmされたらItemsを変更する
            return self, None  # return empty list  # Todo Domain Eventを発行する必要があるか？
        else:
            raise exceptions.UnsupportedStateTransitionException(f'Unsupported State{self.state}')

    def confirm_revise_ticket(self, revise_order_line_items: list[RevisedOrderLineItem]) -> \
            (Ticket, kitchen_domain_event.TicketRevised):

        if self.state == TicketState.REVISION_PENDING:
            self.line_items = revise_order_line_items  # line_itemsを更新
            self.state = self.previous_state  # AWAITING_ACCEPTANCE or ACCEPTED
            return self, kitchen_domain_event.TicketRevised(ticket_id=self.ticket_id,)
        else:
            raise exceptions.UnsupportedStateTransitionException(f'Unsupported State{self.state}')

    def undo_begin_revise_ticket(self) -> (Ticket, list):
        if self.state == TicketState.REVISION_PENDING:
            self.state = self.previous_state  # AWAITING_ACCEPTANCE or ACCEPTED
            return self, None  # return empty list
        else:
            raise exceptions.UnsupportedStateTransitionException(f'Unsupported State{self.state}')

    def accept(self, ready_by: datetime.datetime) -> (Ticket, kitchen_domain_event.TicketAccepted):
        if self.state == TicketState.AWAITING_ACCEPTANCE:
            self.state = TicketState.ACCEPTED
            # Todo: ↑ java sample not implement
            self.accept_time = datetime.datetime.utcnow()
            # Todo: 以下を入れること
            # if self.accept_time >= ready_by:
            #     raise exceptions.IllegalArgumentException(
            #         f'ready_by: {ready_by} is not after now(accept time): {self.accept_time}')
            self.ready_by = ready_by
            return self, kitchen_domain_event.TicketAccepted(ticket_id=self.ticket_id,
                                                             ready_by=ready_by)
        else:
            raise exceptions.UnsupportedStateTransitionException(f'Unsupported State{self.state}')

    # def reject(self):
    #     # No Implement
    #     pass
    #
    # # Todo: 使われてないかもしれない
    # def preparing(self) -> kitchen_domain_event.TicketPreparationStarted:
    #     if self.state == TicketState.ACCEPTED:
    #         self.state = TicketState.PREPARING
    #         self.accept_time = datetime.datetime.utcnow()
    #         return self, kitchen_domain_event.TicketPreparationStarted(ticket_id=self.ticket_id)
    #     else:
    #         raise exceptions.UnsupportedStateTransitionException(f'Unsupported State{self.state}')
    #
    # # Todo: 使われてないかもしれない
    # def ready_for_pickup(self) -> kitchen_domain_event.TicketPreparationCompleted:
    #     if self.state == TicketState.PREPARING:
    #         self.state = TicketState.READY_FOR_PICKUP
    #         self.accept_time = datetime.datetime.utcnow()
    #         return self, kitchen_domain_event.TicketPreparationCompleted(ticket_id=self.ticket_id)
    #     else:
    #         raise exceptions.UnsupportedStateTransitionException(f'Unsupported State{self.state}')
    #
    # # Todo: 使われてないかもしれない
    # def picked_up(self) -> kitchen_domain_event.TicketPickedUp:
    #     if self.state == TicketState.READY_FOR_PICKUP:
    #         self.state = TicketState.PICKED_UP
    #         self.accept_time = datetime.datetime.utcnow()
    #         return self, kitchen_domain_event.TicketPickedUp(ticket_id=self.ticket_id)
    #     else:
    #         raise exceptions.UnsupportedStateTransitionException(f'Unsupported State{self.state}')
    #
    # def change_lineitem_quantity(self):
    #     # No Implement
    #     pass
