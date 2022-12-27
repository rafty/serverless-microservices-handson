# from common import common
from sample_layers.common import common


class Order:

    def __init__(self) -> None:
        self.name = 'Order'

        d = {
            'street1': '9 Amazing View',
            'street2': 'Soi 8',
            'city': 'Oakland',
            'state': 'CA',
            'zip': '94612'
        }
        self.address = common.Address(**d)
