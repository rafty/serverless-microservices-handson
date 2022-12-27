from account_layers.service import service
from account_layers.service import commands
from account_layers.service import events


class Handler:
    def __init__(self, account_repo, account_event_repo):
        self.account_service = service.AccountService(account_repo, account_event_repo)
        self.COMMAND_HANDLER = {
            commands.CreateAccount: getattr(self.account_service, 'create_account'),
        }
        self.SAGACOMMAND_HANDLER = {
            commands.AuthorizeCard: getattr(self.account_service, 'authorize_card'),
            commands.ReverseAuthorizeCard: getattr(self.account_service, 'reverse_authorize_card'),
            commands.ReviseAuthorizeCard: getattr(self.account_service, 'revise_authorize_card'),
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

    def saga_commands_handler(self, cmd: commands.Command):
        try:
            method = self.SAGACOMMAND_HANDLER[cmd.__class__]
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
