import json
import dataclasses
import decimal
from restaurant_layers.common import common
from restaurant_layers.domain import restaurant_model


class Command:
    pass


@dataclasses.dataclass
class CreateRestaurant(Command):
    restaurant_name: str
    restaurant_address: common.Address
    menu_items: restaurant_model.MenuItems

    @classmethod
    def from_json(cls, body_json):
        d = json.loads(body_json, parse_float=decimal.Decimal)
        d['restaurant_address'] = common.Address.from_dict(d['restaurant_address'])
        d['menu_items'] = restaurant_model.MenuItems.from_dict_list(d['menu_items'])
        return cls(**d)


@dataclasses.dataclass
class GetRestaurant(Command):
    restaurant_id: int

    @classmethod
    def from_json(cls, body_json):
        d = json.loads(body_json, parse_float=decimal.Decimal)
        return cls(**d)

