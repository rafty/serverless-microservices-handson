import dataclasses
from consumer_layers.common import common


class DomainEvent:
    pass


@dataclasses.dataclass
class ConsumerCreated(DomainEvent):
    event_id: str
    consumer_id: int
    name: common.PersonName

    def to_dict(self):
        return dataclasses.asdict(self)
