from order_layers.service import service
from order_layers.service import commands
from order_layers.service import events


class Handler:
    def __init__(self, order_repo, order_event_repo, restaurant_replica_repo):

        self.order_service = service.OrderService(order_repo,
                                                  order_event_repo,
                                                  restaurant_replica_repo)
        self.COMMAND_HANDLER = {
            commands.CreateOrder: getattr(self.order_service, 'create_order'),
            commands.GetOrder: getattr(self.order_service, 'find_order_by_id'),
            # commands.CancelOrder: getattr(self.order_service, 'cancel_order'),
            commands.CancelOrder: getattr(self.order_service, 'start_cancel_order_saga'),
            commands.ReviseOrder: getattr(self.order_service, 'start_revise_order_saga'),
        }

        self.SAGACOMMAND_HANDLER = {
            commands.ApproveOrder: getattr(self.order_service, 'approve_order'),
            commands.RejectOrder: getattr(self.order_service, 'reject_order'),
            commands.BeginCancelOrder: getattr(self.order_service, 'begin_cancel'),
            commands.UndoBeginCancelOrder: getattr(self.order_service, 'undo_cancel'),
            commands.ConfirmCancelOrder: getattr(self.order_service, 'confirm_cancel'),
            commands.BeginReviseOrder: getattr(self.order_service, 'begin_revise_order'),
            commands.ConfirmReviseOrder: getattr(self.order_service, 'confirm_revise_order'),
            commands.UndoBeginReviseOrder: getattr(self.order_service, 'undo_begin_revise_order'),
        }

        self.EVENT_HANDLER = {
            events.RestaurantCreated: getattr(self.order_service, 'create_replica_restaurant'),
        }

    def events_handler(self, event: events.Event):
        try:
            method = self.EVENT_HANDLER[event.__class__]
            print(f'event_handler: method: {method}')
            response = method(event)
            return response

        except Exception as e:
            print(str(e))
            raise e

    def commands_handler(self, cmd: commands.Command):
        try:
            method = self.COMMAND_HANDLER[cmd.__class__]
            print(f'commands_handler: method: {method}')
            response = method(cmd)
            return response

        except Exception as e:
            print(str(e))
            raise e

    def saga_commands_handler(self, cmd: commands.Command):
        try:
            method = self.SAGACOMMAND_HANDLER[cmd.__class__]
            print(f'saga_commands_handler: method: {method}')
            response = method(cmd)
            return response

        except Exception as e:
            print(str(e))
            raise e
