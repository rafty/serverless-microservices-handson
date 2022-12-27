from __future__ import annotations  # classの依存関係の許可
import dataclasses
import decimal
import json
from delivery_layer.common import common

"""
Restaurant - Dynamo Item
    PK: RESTAURANTID#{restaurant_id}
    SK: METADATA#{restaurant_id}  # 冪等性担保
    restaurant_id: 1
    restaurant_name: 'Ajenta'
    restaurant_address: {
        "street1": "1 Main Street",
        "street2": "Unit 99",
        "city": "Oakland",
        "state": "CA",
        "zip": "94611"
    }
"""


class Restaurant:
    def __init__(self,
                 restaurant_id: int,
                 restaurant_name: str,
                 restaurant_address: common.Address):

        self.restaurant_id = restaurant_id  # 注意 order_idをdelivery_idにする。
        self.restaurant_name = restaurant_name
        self.restaurant_address = restaurant_address

    @classmethod
    def from_dict(cls, d: dict):
        d['restaurant_address'] = common.Address.from_dict(d['restaurant_address'])
        return cls(**d)

    def to_dict(self):
        def encoder_(o):
            if isinstance(o, Restaurant):
                return o.__dict__  # Todo: ここがポイント
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
