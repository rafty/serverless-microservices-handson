import dataclasses


@dataclasses.dataclass
class DomainEvent:
    account_id: int


@dataclasses.dataclass
class AccountCreated(DomainEvent):
    consumer_id: int
    # card_information: common.CardInformation  # Todo: セキュリティ上、通知しない

    def to_dict(self):
        return dataclasses.asdict(self)
