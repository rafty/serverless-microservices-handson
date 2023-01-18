from __future__ import annotations  # classの依存関係の許可
import dataclasses
import json
import decimal

from restaurant_layers.common import common
from restaurant_layers.domain import restaurant_domain_events


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class MenuItem:
    menu_id: str
    menu_name: str
    price: common.Money

    @classmethod
    def from_dict(cls, d):
        d['price'] = common.Money.from_dict(d['price'])
        return cls(**d)

    def to_dict(self):
        return dataclasses.asdict(self)


class MenuItems:

    def __init__(self, menu_items: list[MenuItem]):
        self.menu_items = menu_items

    def __str__(self):
        return f'<RestaurantMenu {str(id(self))}>'

    @classmethod
    def from_dict_list(cls, d_list):
        menu_items = [MenuItem.from_dict(item) for item in d_list]
        return cls(menu_items=menu_items)

    def to_dict_list(self):
        return [menu_item.to_dict() for menu_item in self.menu_items]


class Restaurant:

    def __init__(self,
                 restaurant_name: str,
                 restaurant_address: common.Address,
                 menu_items: MenuItems,
                 restaurant_id: int = None):

        self.restaurant_id: int = restaurant_id  # Todo: DynamoDBで作成する
        self.restaurant_name: str = restaurant_name
        self.restaurant_address: common.Address = restaurant_address
        self.menu_items: MenuItems = menu_items

    @classmethod
    def from_dict(cls, d: dict):
        d['restaurant_address'] = common.Address.from_dict(d['restaurant_address'])
        d['menu_items'] = MenuItems.from_dict_list(d['menu_items'])
        return cls(**d)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, Restaurant):
                return o.__dict__  # Todo: ここがポイント
            if isinstance(o, MenuItems):  # Enum
                return o.to_dict_list()
            if isinstance(o, MenuItem):  # Enum
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

    @classmethod
    def create(cls, restaurant_id, restaurant_name, restaurant_address, menu_items):
        restaurant = cls(restaurant_id=restaurant_id,
                         restaurant_name=restaurant_name,
                         restaurant_address=restaurant_address,
                         menu_items=menu_items)
        event = restaurant_domain_events.RestaurantCreated(restaurant_id=restaurant.restaurant_id,
                                                           restaurant_name=restaurant.restaurant_name,
                                                           restaurant_address=restaurant.restaurant_address,
                                                           menu_items=restaurant.menu_items)
        return restaurant, event

    # Todo: ↓ Unused ?
    @classmethod
    def create_from_dict(cls, d):
        restaurant = Restaurant.from_dict(d)

        event = restaurant_domain_events.RestaurantCreated(restaurant_name=restaurant.restaurant_name,
                                                           restaurant_address=restaurant.restaurant_address,
                                                           menu_items=restaurant.menu_items.menu_items)

        return restaurant, event
