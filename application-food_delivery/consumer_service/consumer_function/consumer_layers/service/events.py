import dataclasses
import json
import decimal
from consumer_layers.common import common


class Event:
    pass


# @dataclasses.dataclass
# class RestaurantMenuRevised(Event):
#     restaurant_id: int
#     menu_items: list[restaurant_model.MenuItem]
#
#     @classmethod
#     def from_json(cls, j: str):
#         d = json.loads(j, parse_float=decimal.Decimal)
#         return cls(**d)
