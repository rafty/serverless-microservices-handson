import dataclasses
import json
import decimal
from kitchen_layer.common import common
from kitchen_layer.domain import restaurant_model


@dataclasses.dataclass
class Event:
    event_id: int       # 追加 for event_envelope
    timestamp: str      # 追加 for event_envelope


@dataclasses.dataclass
class RestaurantCreated(Event):
    restaurant_id: int
    menu_items: list[restaurant_model.MenuItem]

    @classmethod
    def from_event(cls, event: dict):
        d = dict()
        d['event_id'] = event['event_id']       # 追加 for event_envelope
        d['timestamp'] = event['timestamp']     # 追加 for event_envelope

        d['restaurant_id'] = event['restaurant_id']
        d['menu_items'] = [restaurant_model.MenuItem.from_dict(item)
                           for item in event['menu_items']]
        return cls(**d)


# @dataclasses.dataclass
# class RestaurantMenuRevised(Event):
#     restaurant_id: int
#     menu_items: list[restaurant_model.MenuItem]
#
#     @classmethod
#     def from_json(cls, j: str):
#         d = json.loads(j, parse_float=decimal.Decimal)
#         # d['menu_items'] = restaurant_model.RestaurantMenu.from_dict_list(d['menu_items'])
#         # restaurant_model.Restaurant.fro
#         return cls(**d)
