import dataclasses
import json
import decimal
from order_layers.common import common
from order_layers.domain import restaurant_model


class Event:
    pass


@dataclasses.dataclass
class RestaurantCreated(Event):
    restaurant_id: int
    restaurant_name: str
    menu_items: list[restaurant_model.MenuItem]
    # address: common.Address  # Order Serviceではaddressを使わない

    @classmethod
    def from_event(cls, event: dict):
        d = dict()
        d['restaurant_id'] = event['restaurant_id']
        d['restaurant_name'] = event['restaurant_name']
        d['menu_items'] = [restaurant_model.MenuItem.from_dict(item)
                           for item in event['menu_items']]
        return cls(**d)


@dataclasses.dataclass
class RestaurantMenuRevised(Event):
    restaurant_id: int
    menu_items: list[restaurant_model.MenuItem]

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j, parse_float=decimal.Decimal)
        # d['menu_items'] = restaurant_model.RestaurantMenu.from_dict_list(d['menu_items'])
        # restaurant_model.Restaurant.fro
        return cls(**d)
