# from delivery_layer.adaptors import delivery_repository
# from delivery_layer.adaptors import courier_repository
# from delivery_layer.adaptors import restaurant_replica_repository
from delivery_layer.service import service
from delivery_layer.service import commands
from delivery_layer.service import events


class Handler:

    def __init__(self, delivery_repo, restaurant_repo, courier_repo):

        self.delivery_service = service.DeliveryService(delivery_repo=delivery_repo,
                                                        restaurant_repo=restaurant_repo,
                                                        courier_repo=courier_repo)
        self.EVENT_HANDLER = {
            events.RestaurantCreated: getattr(self.delivery_service, 'create_replica_restaurant'),
            events.OrderCreated: getattr(self.delivery_service, 'create_delivery'),
            events.TicketAccepted: getattr(self.delivery_service, 'schedule_delivery'),
            events.TicketCancelled: getattr(self.delivery_service, 'cancel_delivery'),
        }

        self.COMMAND_HANDLER = {
            commands.CourierAvailability: getattr(self.delivery_service,
                                                  'update_courier_availability'),
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
