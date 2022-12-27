import traceback
from kitchen_layer.service import service
from kitchen_layer.service import commands
from kitchen_layer.service import events


class Handler:
    def __init__(self, kitchen_repo, kitchen_event_repo, restaurant_replica_repo):

        self.kitchen_service = service.KitchenService(kitchen_repo,
                                                      kitchen_event_repo,
                                                      restaurant_replica_repo)
        self.COMMAND_HANDLER = {
            commands.AcceptTicket: getattr(self.kitchen_service, 'accept_ticket')
        }

        self.SAGACOMMAND_HANDLER = {
            commands.CreateTicket: getattr(self.kitchen_service, 'create_ticket'),
            commands.ConfirmCreateTicket: getattr(self.kitchen_service, 'confirm_create_ticket'),
            commands.CancelCreateTicket: getattr(self.kitchen_service, 'cancel_create_ticket'),
            commands.BeginCancelTicket: getattr(self.kitchen_service, 'cancel_ticket'),
            commands.ConfirmCancelTicket: getattr(self.kitchen_service, 'confirm_cancel_ticket'),
            commands.UndoBeginCancelTicket: getattr(self.kitchen_service, 'undo_cancel_ticket'),
            commands.BeginReviseTicket: getattr(self.kitchen_service, 'begin_revise_ticket'),
            commands.UndoBeginReviseTicket: getattr(self.kitchen_service, 'undo_begin_revise_ticket'),
            commands.ConfirmReviseTicket: getattr(self.kitchen_service, 'confirm_revise_ticket'),
        }

        self.EVENT_HANDLER = {
            events.RestaurantCreated: getattr(self.kitchen_service, 'create_replica_restaurant'),
        }

    def events_handler(self, event: events.Event):
        try:
            method = self.EVENT_HANDLER[event.__class__]
            response = method(event)
            return response

        except Exception as e:
            print(str(e))
            raise e

    def commands_handler(self, cmd: commands.Command):
        try:
            method = self.COMMAND_HANDLER[cmd.__class__]
            response = method(cmd)
            return response

        except Exception as e:
            print(str(e))
            raise e

    def saga_commands_handler(self, cmd: commands.Command):
        try:
            method = self.SAGACOMMAND_HANDLER[cmd.__class__]
            response = method(cmd)
            return response

        except Exception as e:
            traceback.print_exc()
            print(str(e))
            raise e
