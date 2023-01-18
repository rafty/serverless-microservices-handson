import dataclasses
from delivery_layer.common import common


@dataclasses.dataclass
class DomainEvent:
    delivery_id: str


@dataclasses.dataclass
class DeliveryCreated(DomainEvent):
    name: common.PersonName

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class DeliveryPickedup(DomainEvent):
    pass

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class DeliveryDelivered(DomainEvent):
    pass

    def to_dict(self):
        return dataclasses.asdict(self)
