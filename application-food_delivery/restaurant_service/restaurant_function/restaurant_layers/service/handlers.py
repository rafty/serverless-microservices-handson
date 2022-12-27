from restaurant_layers.adaptors import restaurant_repository
from restaurant_layers.service import service
from restaurant_layers.service import commands


class Handler:
    def __init__(self, restaurant_repo, restaurant_event_repo):

        self.restaurant_service = service.RestaurantService(restaurant_repo,
                                                            restaurant_event_repo)
        self.COMMAND_HANDLER = {
            commands.CreateRestaurant: getattr(self.restaurant_service, 'create_restaurant'),
            commands.GetRestaurant: getattr(self.restaurant_service, 'find_by_id'),
        }
        self.EVENT_HANDLER = {}

    def commands_handler(self, cmd: commands.Command):
        try:
            method = self.COMMAND_HANDLER[cmd.__class__]
            response = method(cmd)
            return response

        except Exception as e:
            print(str(e))
            raise e
