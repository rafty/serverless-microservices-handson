import pytest
from delivery_layer.domain import restaurant_model
from delivery_layer.service import events
from delivery_layer.service import service
from delivery_layer.adaptors import restaurant_replica_repository


restaurant_repo = restaurant_replica_repository.DynamoDbRepository()
order_service = service.DeliveryService(delivery_repo=None,
                                        courier_repo=None,
                                        restaurant_repo=restaurant_repo)


@pytest.fixture
def restaurant_created_event_from_eventbridge():
    d = {
        "version": "0",
        "id": "7497d71c-451c-1342-3bac-3a8f9a2d5fe4",
        "detail-type": "RestaurantCreated",
        "source": "com.restaurant.created",
        "account": "338456725408",
        "time": "2022-12-20T09:20:27Z",
        "region": "ap-northeast-1",
        "resources": [],
        "detail": {
            "event_id": "03430a1723d840ad93c11b944d85b503",
            "restaurant_id": 27,
            "restaurant_address": {
                "zip": "94611",
                "city": "Oakland",
                "street1": "1 Main Street",
                "street2": "Unit 99",
                "state": "CA"
            },
            "menu_items": [
                {
                    "price": {
                        "currency": "JPY",
                        "value": 800
                    },
                    "menu_name": "Curry Rice",
                    "menu_id": "000001"
                },
                {
                    "price": {
                        "currency": "JPY",
                        "value": 1000
                    },
                    "menu_name": "Hamburger",
                    "menu_id": "000002"
                },
                {
                    "price": {
                        "currency": "JPY",
                        "value": 700
                    },
                    "menu_name": "Ramen",
                    "menu_id": "000003"
                }
            ],
            "restaurant_name": "skylark",
            "channel": "RestaurantCreated"
        }
    }
    return d


def test_create_restaurant(restaurant_created_event_from_eventbridge):
    event = events.RestaurantCreated.from_event(
        restaurant_created_event_from_eventbridge['detail'])

    # Assert That NO Exception Is Raised
    try:
        order_service.create_replica_restaurant(event)
    except Exception as e:
        assert False, f'order_service.create_replica_restaurant() raised an Exception {e}'

