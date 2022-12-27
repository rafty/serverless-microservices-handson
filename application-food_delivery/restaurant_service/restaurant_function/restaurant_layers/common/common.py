from __future__ import annotations  # classの依存関係の許可
import dataclasses
import decimal


@dataclasses.dataclass(frozen=True, order=True)
class Money:
    # value: int
    value: decimal.Decimal | int  # Todo: Decimalに変更
    currency: str = 'JPY'

    def __add__(self, other: Money) -> Money:
        return Money(self.value + other.value)

    def __sub__(self, other: Money) -> Money:
        return Money(self.value - other.value)

    def __mul__(self, other: int) -> Money:
        return Money(self.value * other)

    def to_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclasses.dataclass(frozen=True)
class Address:
    street1: str
    street2: str
    city: str
    state: str
    zip: str

    def to_dict(self):
        return dataclasses.asdict(self)

    # Todo: classmethodは最後に書く必要がある？ 確認すること
    @classmethod
    def from_dict(cls, d):
        return cls(**d)
