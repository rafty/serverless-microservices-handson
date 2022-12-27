import json
from kitchen_layer.domain import ticket_model
from kitchen_layer.domain import restaurant_model
from kitchen_layer.service import events
from kitchen_layer.service import commands
from kitchen_layer.common import common


class KitchenService:

    """
    1. create_ticket      CREATE_PENDING
    2. confirm_create     AWAITING_ACCEPTANCE
    3. accept             ACCEPTED
    4. preparing          PREPARING             # Todo: 使われてないかもしれない
    5. ready_for_pickup   READY_FOR_PICKUP      # Todo: 使われてないかもしれない
    6. picked_up          PICKED_UP             # Todo: 使われてないかもしれない
    異常系 cancel          AWAITING_ACCEPTANCE or ACCEPTED -> CANCEL_PENDING
    異常系 confirm_cancel  CANCEL_PENDING -> CANCELLED
    begin_revise_order    AWAITING_ACCEPTANCE or ACCEPTED -> REVISION_PENDING
    """

    def __init__(self, kitchen_repo, kitchen_event_repo, restaurant_replica_repo):
        self.kitchen_repo = kitchen_repo
        self.kitchen_event_repo = kitchen_event_repo
        self.restaurant_replica_repo = restaurant_replica_repo

    # ------------------------------------------------------------
    # for Restaurant Service Events
    # ------------------------------------------------------------
    def create_replica_restaurant(self, event: events.RestaurantCreated):
        restaurant = restaurant_model.Restaurant(event.restaurant_id, event.menu_items)
        self.restaurant_replica_repo.save(restaurant)

    # ------------------------------------------------------------
    # Create Saga - action: CREATE_TICKET
    # ------------------------------------------------------------
    # Todo: from Create Order Saga
    def create_ticket(self, cmd: commands.CreateTicket):

        # Todo: オリジナル実装をすること
        #  ・・・sampleにはこのロジックはない。
        #  menu_idがあるかどうかチェックし、なければTicketCreationFailedを返す。
        #  Ticketドメインロジックではない。
        #  RestaurantDomainとTicketの間の処理なので、ServiceLayerで実装する？

        print(f'service.py create_ticket: {cmd}')
        ticket, events_ = ticket_model.Ticket.create_ticket(ticket_id=cmd.ticket_id,
                                                            restaurant_id=cmd.restaurant_id,
                                                            line_items=cmd.line_items)

        # Todo: 両方のsave()をTransactionで・・・
        self.kitchen_repo.save(ticket)
        self.kitchen_event_repo.save(events_)  # To TicketEvent Channel
        # return True
        return {'ticket_id': ticket.ticket_id}  # Todo: Sagaで後続がticket_id使うためリターンする

    # Todo: from Saga 補償トランザクション
    def cancel_create_ticket(self, cmd: commands.CancelCreateTicket):

        ticket: ticket_model.Ticket = self.kitchen_repo.find_by_id(cmd.ticket_id)

        if ticket:
            ticket_, events_ = ticket.cancel_create()
            self.kitchen_repo.save(ticket_)
            self.kitchen_event_repo.save(events_)
            return True  # Todo: Saga reply 正常
        else:
            raise common.exceptions.TicketNotFoundException(
                f'TicketNotFound: ticket_id: {cmd.ticket_id}')

    # Todo: from Create Order Saga
    def confirm_create_ticket(self, cmd: commands.ConfirmCreateTicket):
        ticket: ticket_model.Ticket = self.kitchen_repo.find_by_id(cmd.ticket_id)

        if ticket:
            ticket_, events_ = ticket.confirm_create()
            self.kitchen_repo.save(ticket_)
            self.kitchen_event_repo.save(events_)
            return True  # Todo: Saga reply 正常
        else:
            raise common.exceptions.TicketNotFoundException(
                f'TicketNotFound: ticket_id: {cmd.ticket_id}')

    # ---------------------------------------------------------------
    # Cancel Order Saga
    # ---------------------------------------------------------------
    def cancel_ticket(self, cmd: commands.BeginCancelTicket):
        ticket: ticket_model.Ticket = self.kitchen_repo.find_by_id(cmd.ticket_id)

        if ticket:
            ticket_, events_ = ticket.cancel()
            self.kitchen_repo.save(ticket_)
            self.kitchen_event_repo.save(events_)
            return True  # Todo: Saga reply 正常
        else:
            raise common.exceptions.TicketNotFoundException(
                f'TicketNotFound: ticket_id: {cmd.ticket_id}')

    def confirm_cancel_ticket(self, cmd: commands.ConfirmCancelTicket):
        ticket: ticket_model.Ticket = self.kitchen_repo.find_by_id(cmd.ticket_id)

        if ticket:
            ticket_, events_ = ticket.confirm_cancel()
            self.kitchen_repo.save(ticket_)
            self.kitchen_event_repo.save(events_)
            return True  # Todo: Saga reply 正常
        else:
            raise common.exceptions.TicketNotFoundException(
                f'TicketNotFound: ticket_id: {cmd.ticket_id}')

    # Cancel Order Saga - 補償トランザクション
    def undo_cancel_ticket(self, cmd: commands.UndoBeginCancelTicket):
        ticket: ticket_model.Ticket = self.kitchen_repo.find_by_id(cmd.ticket_id)

        if ticket:
            ticket_, events_ = ticket.undo_cancel()
            self.kitchen_repo.save(ticket_)
            self.kitchen_event_repo.save(events_)
            return True  # Todo: Saga reply 正常
        else:
            raise common.exceptions.TicketNotFoundException(
                f'TicketNotFound: ticket_id: {cmd.ticket_id}')

    # ---------------------------------------------------------------
    # Revise Order Saga
    # ---------------------------------------------------------------
    def begin_revise_ticket(self, cmd: commands.BeginReviseTicket):
        ticket: ticket_model.Ticket = self.kitchen_repo.find_by_id(cmd.ticket_id)

        if ticket:
            # Todo: verify restaurant id  -> 現時点でrestaurant_idは使っていない
            ticket_, events_ = ticket.begin_revise_ticket(cmd.revised_order_line_items)
            self.kitchen_repo.save(ticket_)
            self.kitchen_event_repo.save(events_)
            return True  # Todo: Saga reply 正常
        else:
            raise common.exceptions.TicketNotFoundException(
                f'TicketNotFound: ticket_id: {cmd.ticket_id}')

    def confirm_revise_ticket(self, cmd: commands.ConfirmReviseTicket):
        ticket: ticket_model.Ticket = self.kitchen_repo.find_by_id(cmd.ticket_id)

        if ticket:
            # Todo: verify restaurant id  -> 現時点でrestaurant_idは使っていない
            ticket_, events_ = ticket.confirm_revise_ticket(cmd.revised_order_line_items)
            self.kitchen_repo.save(ticket_)
            self.kitchen_event_repo.save(events_)
            return True
        else:
            raise common.exceptions.TicketNotFoundException(
                f'TicketNotFound: ticket_id: {cmd.ticket_id}')

    # 補償トランザクション
    def undo_begin_revise_ticket(self, cmd: commands.UndoBeginReviseTicket):
        ticket: ticket_model.Ticket = self.kitchen_repo.find_by_id(cmd.ticket_id)

        if ticket:
            # Todo: verify restaurant id  -> 現時点でrestaurant_idは使っていない
            ticket_, events_ = ticket.undo_begin_revise_ticket()
            self.kitchen_repo.save(ticket_)
            if events_:
                self.kitchen_event_repo.save(events_)
            return True  # Todo: Saga reply 正常
        else:
            raise common.exceptions.TicketNotFoundException(
                f'TicketNotFound: ticket_id: {cmd.ticket_id}')

    # path="/tickets/{ticketId}/accept" POST
    def accept_ticket(self, cmd: commands.AcceptTicket):
        ticket: ticket_model.Ticket = self.kitchen_repo.find_by_id(cmd.ticket_id)
        if ticket:
            ticket_, events_ = ticket.accept(cmd.ready_by)
            self.kitchen_repo.save(ticket_)
            self.kitchen_event_repo.save(events_)
            return True  # Todo: REST reply 正常
        else:
            raise common.exceptions.TicketNotFoundException(
                f'TicketNotFound: ticket_id: {cmd.ticket_id}')

    # # ------------------------------
    # # from Restaurant Service Event
    # # ------------------------------
    # def create_menu(self, event: events.RestaurantCreated):
    #
    #     restaurant = restaurant_model.Restaurant(event.restaurant_id,
    #                                              event.menu_items)
    #     self.restaurant_replica_repo.save(restaurant)
    #     return
    #
    # def revise_menu(self, event: events.RestaurantMenuRevised):
    #
    #     # Todo: ticket_idからrestaurantをqueryする
    #     #       ticket_id　と　restaurant は結びつかない。java sampleが異常！
    #     # restaurant: restaurant_model.Restaurant =\
    #                                   self.restaurant_repo.find_by_id(event.ticket_id)
    #     # restaurant.revise_menu(revise_details=event.menu)
    #     return
