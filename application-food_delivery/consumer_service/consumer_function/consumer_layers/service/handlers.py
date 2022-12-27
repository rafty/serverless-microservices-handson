from consumer_layers.service import service
from consumer_layers.service import commands
from consumer_layers.service import events


class Handler:
    def __init__(self, consumer_repo, consumer_event_repo):
        self.consumer_service = service.ConsumerService(consumer_repo, consumer_event_repo)
        self.COMMAND_HANDLER = {
            commands.CreateConsumer: getattr(self.consumer_service, 'create_consumer'),
            commands.GetConsumer: getattr(self.consumer_service, 'get_consumer_by_id'),
        }
        self.SAGACOMMAND_HANDLER = {
            commands.ValidateOrderForConsumer: getattr(self.consumer_service,
                                                       'validate_order_for_consumer'),
        }
        self.EVENT_HANDLER = {}

    def saga_commands_handler(self, cmd: commands.Command):
        try:
            method = self.SAGACOMMAND_HANDLER[cmd.__class__]
            response = method(cmd)
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

    def events_handler(self, event: events.Event):
        try:
            method = self.EVENT_HANDLER[event.__class__]
            response = method(event)
            return response

        except Exception as e:
            print(str(e))
            raise e
