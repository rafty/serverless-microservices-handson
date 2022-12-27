from __future__ import annotations  # classの依存関係の許可
import dataclasses
import decimal
import json
from order_layers.common import common
from order_layers.common import exception


@dataclasses.dataclass(unsafe_hash=True)
class MenuItem:
    menu_id: str
    menu_name: str
    price: common.Money

    @classmethod
    def from_dict(cls, d):

        d['price'] = common.Money.from_dict(d['price'])
        return cls(**d)


class Restaurant:

    def __init__(self,
                 restaurant_id: int,
                 restaurant_name: str,
                 menu_items: list[MenuItem]):

        self.restaurant_id: int = restaurant_id
        self.restaurant_name: str = restaurant_name
        self.menu_items: list[MenuItem] = menu_items

    @classmethod
    def from_dict(cls, d: dict):
        d['menu_items'] = [MenuItem.from_dict(item) for item in d['menu_items']]
        return cls(**d)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, Restaurant):
                return o.__dict__
            if isinstance(o, MenuItem):
                return dataclasses.asdict(o)
            if isinstance(o, common.Money):
                return dataclasses.asdict(o)
            if isinstance(o, decimal.Decimal):
                if int(o) == o:
                    return int(o)
                else:
                    return float(o)
            raise TypeError(f'{repr(o)} is not serializable')

        d = json.loads(json.dumps(self, default=encoder_))
        return d

    def find_menu_item(self, menu_id: str) -> MenuItem:
        menus = [menu for menu in self.menu_items if menu.menu_id == menu_id]
        if len(menus) == 0:
            raise exception.MenuItemNotFound(f'MenuItemNotFound: {menu_id}')
        else:
            return menus[0]
