from account_layers.domain import account_model
from account_layers.service import commands
from account_layers.common import exceptions
from account_layers.service.domain_event_envelope import DomainEventEnvelope


class AccountService:

    def __init__(self, account_repo, account_event_repo):
        self.account_repo = account_repo
        self.account_event_repo = account_event_repo

    def create_account(self, cmd: commands.CreateAccount):
        account, domain_event = account_model.Account.create(consumer_id=cmd.consumer_id,
                                                             card_information=cmd.card_information)
        self.account_repo.save(account)

        self.account_event_repo.save(event=DomainEventEnvelope.wrap(domain_event))

        return account

    def get_account(self, cmd: commands.GetAccount):
        accounts = self.account_repo.find_by_id(consumer_id=cmd.consumer_id)
        return accounts

    # -------------------------------------------------------------------------
    # Create Order Saga
    # -------------------------------------------------------------------------
    def authorize_card(self, cmd: commands.AuthorizeCard):

        account = self.account_repo.find_by_id(consumer_id=cmd.consumer_id)
        if account:
            result = account.authorize_card(cmd.money_total)
            return result
        else:
            raise exceptions.AccountNotFoundException(
                f'AccountNotFound: consumer_id: {cmd.consumer_id}')

    # -------------------------------------------------------------------------
    # Cancel Order Saga
    # -------------------------------------------------------------------------
    def reverse_authorize_card(self, cmd: commands.ReverseAuthorizeCard):

        account: account_model.Account = self.account_repo.find_by_id(consumer_id=cmd.consumer_id)
        if account:
            result = account.reverse_authorize_card(consumer_id=cmd.consumer_id,
                                                    order_id=cmd.order_id,
                                                    money_total=cmd.money_total)
            return result
        else:
            raise exceptions.AccountNotFoundException(
                f'AccountNotFound: consumer_id: {cmd.consumer_id}')

    # -------------------------------------------------------------------------
    # Revise Order Saga
    # -------------------------------------------------------------------------
    def revise_authorize_card(self, cmd: commands.ReviseAuthorizeCard):

        print(f'revise_authorize_card cmd: {cmd}')

        account: account_model.Account = self.account_repo.find_by_id(consumer_id=cmd.consumer_id)
        if account:

            print(f'PRE account.revise_authorize_card() cmd: {cmd}')
            result = account.revise_authorize_card(consumer_id=cmd.consumer_id,
                                                   order_id=cmd.order_id,
                                                   money_total=cmd.money_total)
            return result
        else:
            raise exceptions.AccountNotFoundException(
                f'AccountNotFound: consumer_id: {cmd.consumer_id}')

