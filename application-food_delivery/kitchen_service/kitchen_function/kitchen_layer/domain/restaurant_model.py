from __future__ import annotations
import dataclasses
import decimal
import json
from kitchen_layer.common import common
from kitchen_layer.common import exceptions
from kitchen_layer.domain import ticket_model


@dataclasses.dataclass(unsafe_hash=True)
class MenuItem:
    menu_id: str
    menu_name: str
    price: common.Money

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class RestaurantMenu:

    def __init__(self, menu_items: list[MenuItem]):
        self.menu_items = menu_items

    @classmethod
    def from_dict_list(cls, d_list):
        """
        [
            {
                "menu_id": "000001",
                "name": "Curry Rice",
                "price": 800
            },
            {
                "menu_id": "000002",
                "name": "Hamburger",
                "price": 1000
            },
            {
                "menu_id": "000003",
                "name": "Ramen",
                "price": 700
            }
        ]
        """
        menu_items = [MenuItem.from_dict(item) for item in d_list]
        return cls(menu_items=menu_items)

    def to_dict_list(self):
        return [dataclasses.asdict(item) for item in self.menu_items]


class Restaurant:

    def __init__(self,
                 restaurant_id: int,
                 menu_items: list[MenuItem]):

        self.restaurant_id: int = restaurant_id
        self.menu_items: list[MenuItem] = menu_items

    @classmethod
    def create(cls,
               restaurant_id: int,
               menu_items: list[MenuItem]):

        restaurant = cls(restaurant_id=restaurant_id,
                         menu_items=menu_items)
        return restaurant

    @classmethod
    def from_dict(cls, d: dict):
        # Todo: 必要なところだけ変える
        d['menu_items'] = [MenuItem(item) for item in d['menu_items']]
        return cls(**d)

    def to_dict(self):
        def restaurant_encoder(o):
            if isinstance(o, Restaurant):
                return o.__dict__
            if isinstance(o, MenuItem):
                return dataclasses.asdict(o)
            if isinstance(o, common.Money):
                return dataclasses.asdict(o)
            if isinstance(o, decimal.Decimal):
                return o  # Decimalのまま返す
            raise TypeError(f'{repr(o)} is not serializable')

        dict_ = json.loads(json.dumps(self, default=restaurant_encoder))
        return dict_

    def revise_menu(self, revise_details: RestaurantMenu):
        raise exceptions.UnsupportedOperationException('revise_menu()')

    # def verify_restaurant_details(self, ticket_details: ticket_model.TicketDetails):
    def verify_restaurant_details(self, line_items: list[ticket_model.TicketLineItem]):
        pass
        # Todo: not Implement in sample java
