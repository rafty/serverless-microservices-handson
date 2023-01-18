from order_history_layers.service import service
from order_history_layers.service import commands
from order_history_layers.service import events


class Handler:

    def __init__(self, order_history_dao):
        self.order_history_service = service.OrderHistoryService(order_history_dao)

        self.COMMAND_HANDLER = {
            # GET /orders/{order_id}
            commands.GetOrder: getattr(self.order_history_service, 'get_order'),
            # GET /orders
            commands.GetOrders: getattr(self.order_history_service, 'get_order_history'),
        }

        self.EVENT_HANDLER = {
            events.OrderCreated: getattr(self.order_history_service, 'create_order'),
            events.OrderAuthorized: getattr(self.order_history_service, 'update_order_state'),
            events.OrderRejected: getattr(self.order_history_service, 'update_order_state'),
            events.OrderCancelled: getattr(self.order_history_service, 'update_order_state'),
            events.DeliveryPickedup: getattr(self.order_history_service, 'update_delivery_state'),
            events.DeliveryDelivered: getattr(self.order_history_service, 'update_delivery_state'),
        }

    def events_handler(self, event: events.DomainEventEnvelope):
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
