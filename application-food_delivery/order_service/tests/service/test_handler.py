from order_layers.service import commands
from order_layers.domain import order_model
from order_layers.common import common
from order_layers.service import handlers
from order_layers.adaptors import order_repository
from order_layers.adaptors import order_event_repository

# request_json = """
# {
#     "name": "skylark",
#     "address": {
#         "street1": "1 Main Street",
#         "street2": "Unit 99",
#         "city": "Oakland",
#         "state": "CA",
#         "zip": "94611"
#     },
#     "menu": [
#         {
#             "menu_id": "000001",
#             "name": "Curry Rice",
#             "price": {
#                 "value": 800,
#                 "currency": "JPY"
#             }
#         },
#         {
#             "menu_id": "000002",
#             "name": "Hamburger",
#             "price": {
#                 "value": 1000,
#                 "currency": "JPY"
#             }
#         },
#         {
#             "menu_id": "000003",
#             "name": "Ramen",
#             "price": {
#                 "value": 700,
#                 "currency": "JPY"
#             }
#         }
#     ]
# }
# """

create_order_request_json = """{
    "consumer_id": 1511300065921,
    "restaurant_id": 1,
    "delivery_time": "2022-11-30T05:00:30.001000Z",
    "delivery_address": {
        "street1": "9 Amazing View",
        "street2": "Soi 7",
        "city": "Oakland",
        "state": "CA",
        "zip": "94612"
    },
    "line_items": [{
        "menu_id": "000001",
        "quantity": 5
    }]
}"""


def test_create_order():
    order_repo = order_repository.DynamoDbOrderRepository()
    order_event_repo = order_event_repository.DynamoDbOrderEventRepository()
    restaurant_repo = None  # Todo: やれ！
    create_order_cmd = command.CreateOrder.from_json(create_order_request_json)
    order = handlers.commands_handler(cmd=create_order_cmd,
                                      order_repo=order_repo,
                                      order_event_repo=order_event_repo,
                                      restaurant_repo=restaurant_repo)

    assert isinstance(order, model.Order)
    assert isinstance(order.order_id, str)
    assert isinstance(order.delivery_information, model.DeliveryInformation)
    assert isinstance(order.order_line_items, model.OrderLineItems)
    assert order.order_state == model.OrderState.APPROVAL_PENDING
    # ・・・
