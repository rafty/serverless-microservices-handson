from __future__ import annotations  # classの依存関係の許可
import dataclasses
import decimal
import datetime
from account_layers.common import exceptions


@dataclasses.dataclass(frozen=True, order=True, unsafe_hash=True)  # Todo 比較のためにhash値を使えるようにする！
class Money:
    # value: int
    value: decimal.Decimal | int  # Todo: Decimalに変更
    currency: str = 'JPY'

    def __add__(self, other: Money) -> Money:
        if self.currency == other.currency:
            return Money(self.value + other.value, other.currency)
        else:
            raise exceptions.InvalidCurrency(f'{self.currency}')

    def __sub__(self, other: Money) -> Money:
        if self.currency == other.currency:
            return Money(self.value - other.value, other.currency)
        else:
            raise exceptions.InvalidCurrency(f'{self.currency}')

    def __mul__(self, other: int) -> Money:
        return Money(self.value * other, self.currency)

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

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclasses.dataclass(frozen=True)
class PersonName:
    first_name: str
    last_name: str

    def to_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclasses.dataclass(frozen=True)
class CardInformation:
    card_number: str
    expiry_date: datetime.datetime

    def to_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d):
        d['expiry_date'] = datetime.datetime.strptime(d['expiry_date'], '%Y-%m-%dT%H:%M:%S.%fZ')
        return cls(**d)
