import dataclasses
from account_layers.common import common


class DomainEvent:
    pass


@dataclasses.dataclass
class AccountCreated(DomainEvent):
    event_id: str
    consumer_id: int
    account_id: int
    # card_information: common.CardInformation  # Todo: セキュリティ上、通知しない

    def to_dict(self):
        return dataclasses.asdict(self)
