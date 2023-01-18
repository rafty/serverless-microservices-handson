import pytest
from order_history_layers.model import order_model

#
# @pytest.fixture
# def delivery_information_master_dict():
#     d = {
#         'delivery_time': '2022-11-30T05:00:30.001000Z',
#         'delivery_address': {
#             'street1': '9 Amazing View',
#             'street2': 'Soi 8',
#             'city': 'Oakland',
#             'state': 'CA',
#             'zip': '94612'
#         }
#     }
#     return d
#
#
# def test_delivery_information_from_dict_and_to_dict(delivery_information_master_dict):
#
#     delivery_information = order_model.DeliveryInformation.from_dict(
#         delivery_information_master_dict)
#
#     assert delivery_information.delivery_time == delivery_information_master_dict['delivery_time']
#     assert delivery_information.delivery_address.street1 == '9 Amazing View'
#
#     dict_ = delivery_information.to_dict()
#
#     assert dict_['delivery_time'] == '2022-11-30T05:00:30.001000Z'
#     assert dict_['delivery_address']['state'] == 'CA'
#
#
# @pytest.fixture
# def order_line_items_master_list():
#     line_items = [
#         {
#             "menu_id": "000001",
#             "name": "Curry Rice",
#             "price": {"value": 800, "currency": "JPY"},
#             'quantity': 3,
#         },
#         {
#             "menu_id": "000002",
#             "name": "Hamburger",
#             "price": {"value": 1000, "currency": "JPY"},
#             'quantity': 2,
#         },
#         {
#             "menu_id": "000003",
#             "name": "Ramen",
#             "price": {"value": 700, "currency": "JPY"},
#             'quantity': 1,
#         }
#     ]
#     return line_items
#
#
# def test_order_line_items_from_dict(order_line_items_master_list):
#     order_line_items = order_model.OrderLineItems.from_dict_list(order_line_items_master_list)
#
#     assert order_line_items is not None
#
#     order_line_items_dict_list = order_line_items.to_dict_list()
#
#     for item_dict in order_line_items_dict_list:
#         assert item_dict['price']['value'] in [800, 1000, 700]


@pytest.fixture
def order_master_dict():
    d = {
        'consumer_id': 1511300065921,
        'restaurant_id': 1,
        'delivery_information': {
           'delivery_time': "2022-11-30T05:00:30.001000Z",
           'delivery_address': {
                'street1': '9 Amazing View',
                'street2': None,
                'city': 'Oakland',
                'state': 'CA',
                'zip': '94612',
            },
        },
        'order_line_items': [
            {
                "menu_id": "000001",
                "name": "Curry Rice",
                "price": {"value": 800, "currency": "JPY"},
                'quantity': 3,
            },
            {
                "menu_id": "000002",
                "name": "Hamburger",
                "price": {"value": 1000, "currency": "JPY"},
                'quantity': 2,
            },
            {
                "menu_id": "000003",
                "name": "Ramen",
                "price": {"value": 700, "currency": "JPY"},
                'quantity': 1,
            }
        ],
    }
    return d


def test_order_from_dict(order_master_dict):

    order = order_model.Order.from_dict(order_master_dict)

    assert order.consumer_id == 1511300065921

    order_dict = order.to_dict()

    assert order_dict['consumer_id'] == 1511300065921
