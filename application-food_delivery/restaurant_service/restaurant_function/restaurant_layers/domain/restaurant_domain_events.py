from __future__ import annotations
import dataclasses
import json
import decimal
from restaurant_layers.common import common
from restaurant_layers.domain import restaurant_model


@dataclasses.dataclass
class DomainEvent:
    restaurant_id: int


@dataclasses.dataclass
class RestaurantCreated(DomainEvent):
    restaurant_name: str
    restaurant_address: common.Address
    menu_items: list[restaurant_model.MenuItem]

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, RestaurantCreated):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, restaurant_model.MenuItems):  # Enum
                return o.to_dict_list()
            if isinstance(o, restaurant_model.MenuItem):  # Enum
                return o.to_dict()
            if isinstance(o, common.Address):
                return dataclasses.asdict(o)
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_))
        return d
