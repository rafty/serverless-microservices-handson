import json
import dataclasses
import decimal
from restaurant_layers.common import common
from restaurant_layers.domain import restaurant_model


class Response:
    pass


@dataclasses.dataclass
class CreateRestaurantResponse(Response):
    restaurant_id: int

    @classmethod
    def from_obj(cls, restaurant: restaurant_model.Restaurant):
        return cls(restaurant_id=restaurant.restaurant_id)

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class GetRestaurantResponse(Response):
    restaurant_id: int
    restaurant_name: str
    restaurant_address: common.Address
    menu_items: restaurant_model.Restaurant

    @classmethod
    def from_obj(cls, restaurant: restaurant_model.Restaurant):
        return cls(restaurant_id=restaurant.restaurant_id,
                   restaurant_name=restaurant.restaurant_name,
                   restaurant_address=restaurant.restaurant_address,
                   menu_items=restaurant.menu_items)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, GetRestaurantResponse):
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

        d = json.loads(json.dumps(self, default=encoder_), parse_float=decimal.Decimal)
        return d
