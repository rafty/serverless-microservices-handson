import dataclasses
from consumer_layers.common import common


@dataclasses.dataclass
class DomainEvent:
    consumer_id: int


@dataclasses.dataclass
class ConsumerCreated(DomainEvent):
    name: common.PersonName

    def to_dict(self):
        return dataclasses.asdict(self)
