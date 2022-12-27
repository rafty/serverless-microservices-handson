import dataclasses
import decimal


@dataclasses.dataclass(frozen=True)
class Address:
    street1: str
    street2: str
    city: str
    state: str
    zip: str

    def to_dict(self):
        return dataclasses.asdict(self)


