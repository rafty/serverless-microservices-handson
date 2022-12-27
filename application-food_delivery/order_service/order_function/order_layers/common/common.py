from __future__ import annotations  # classの依存関係の許可
import dataclasses
import decimal
from order_layers.common import exception


@dataclasses.dataclass(frozen=True, order=True, unsafe_hash=True)  # Todo 比較のためにhash値を使えるようにする！
class Money:
    value: decimal.Decimal | int  # Decimal or int
    currency: str = 'JPY'

    def __add__(self, other: Money) -> Money:
        if self.currency == other.currency:
            return Money(self.value + other.value, other.currency)
        else:
            raise exception.InvalidCurrency(f'{self.currency}')

    def __sub__(self, other: Money) -> Money:
        if self.currency == other.currency:
            return Money(self.value - other.value, other.currency)
        else:
            raise exception.InvalidCurrency(f'{self.currency}')

    def __mul__(self, other: int) -> Money:
        return Money(self.value * other, self.currency)

    def to_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclasses.dataclass(unsafe_hash=True, frozen=True)
class Address:
    street1: str
    street2: str
    city: str
    state: str
    zip: str

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    def to_dict(self):
        return dataclasses.asdict(self)


