import pytest
# from order_layers.domain import restaurant_model
from order_history_layers.service import events
from order_history_layers.service import service
from order_history_layers.store import restaurant_replica_repository


restaurant_repo = restaurant_replica_repository.DynamoDbRepository()
order_service = service.OrderHistoryService(order_repo=None,
                                            order_event_repo=None,
                                            restaurant_replica_repo=restaurant_repo)


@pytest.fixture
def restaurant_created_event_from_eventbridge():
    d = {
        "version": "0",
        "id": "45b53d2d-7822-eaa1-9bcd-08cf6de6a8c7",
        "detail-type": "RestaurantCreated",
        "source": "com.restaurant.created",
        "account": "123456789012",
        "time": "2022-12-05T04:26:52Z",
        "region": "ap-northeast-1",
        "resources": [],
        "detail": {
            "event_id": "8eae2129e81d40878393ec2f69fc8939",
            "restaurant_id": 1,
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



