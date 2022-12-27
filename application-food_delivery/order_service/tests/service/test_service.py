import pytest
from order_layers.domain import order_model
from order_layers.service import commands
from order_layers.service import service
from order_layers.adaptors import restaurant_replica_repository
from order_layers.adaptors import order_repository
from order_layers.adaptors import order_event_repository


restaurant_repo = restaurant_replica_repository.DynamoDbRepository()
order_repo = order_repository.DynamoDbRepository()
order_event_repo = order_event_repository.DynamoDbRepository()
order_service = service.OrderService(order_repo=order_repo,
                                     order_event_repo=order_event_repo,
                                     restaurant_replica_repo=restaurant_repo)


@pytest.fixture
def order_master_json():
    j = """{
        "consumer_id": 1511300065921,
        "restaurant_id": 1,
        "delivery_information": {
           "delivery_time": "2022-11-30T05:00:30.001000Z",
           "delivery_address": {
                "street1": "9 Amazing View",
                "street2": "Soi 8",
                "city": "Oakland",
                "state": "CA",
                "zip": "94612"
            }
        },
        "order_line_items": [
            {
                "menu_id": "000001",
                "quantity": 3
            },
            {
                "menu_id": "000002",
                "quantity": 2
            },
            {
                "menu_id": "000003",
                "quantity": 1
            }
        ]
    }"""
    return j


def test_order_create(order_master_json):

    cmd = commands.CreateOrder.from_json(order_master_json)

    order = order_service.create_order(cmd=cmd)

    assert order.order_state == order_model.OrderState.APPROVAL_PENDING
    assert order.consumer_id == cmd.consumer_id
    assert order.restaurant_id == cmd.restaurant_id
    assert order.order_line_items.line_items[0].menu_id == cmd.order_line_items[0].menu_id
    assert order.order_line_items.line_items[0].quantity == cmd.order_line_items[0].quantity
    assert order.delivery_information.delivery_address == cmd.delivery_information.delivery_address
    assert order.lock_version == 1


# @pytest.fixture
# def order_mother():
#     cmd = command.CreateOrder.from_json(create_order_request_json)
#     order_repo = order_repository.DynamoDbOrderRepository()
#     order_event_repo = order_event_repository.DynamoDbOrderEventRepository()
#     restaurant_repo = None  # Todo: 後で対処
#
#     order = service.OrderService.create(cmd=cmd,
#                                         order_repo=order_repo,
#                                         order_event_repo=order_event_repo,
#                                         restaurant_repo=restaurant_repo)
#     return order, cmd, order_repo
#
#
# def test_create_order(order_mother: (model.Order, command.CreateOrder)):
#     order = order_mother[0]
#     cmd = order_mother[1]
#
#     assert order.order_state == model.OrderState.APPROVAL_PENDING
#     assert order.consumer_id == cmd.consumer_id
#     assert order.restaurant_id == cmd.restaurant_id
#     assert order.order_line_items.line_items[0].menu_id == cmd.line_items[0].menu_id
#     assert order.order_line_items.line_items[0].quantity == cmd.line_items[0].quantity
#     assert order.delivery_information.delivery_address == cmd.delivery_information.delivery_address
#
#
# def test_approve_order(order_mother):
#     order = order_mother[0]
#     cmd = order_mother[1]
#     order_repo = order_mother[2]
#
#     response = service.OrderService.approve_order(order_id=order.order_id,
#                                                   order_repo=order_repo,
#                                                   order_aggregate_event_pub=None)
#
#     assert response != None
