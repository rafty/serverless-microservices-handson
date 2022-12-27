import dataclasses
from delivery_layer.common import common


class DomainEvent:
    pass


@dataclasses.dataclass
class DeliveryCreated(DomainEvent):
    delivery_id: int
    name: common.PersonName

    def to_dict(self):
        return dataclasses.asdict(self)
