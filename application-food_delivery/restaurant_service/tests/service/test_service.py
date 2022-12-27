import pytest
from restaurant_layers.service import service
from restaurant_layers.service import commands
from restaurant_layers.domain import restaurant_model
from restaurant_layers.adaptors import restaurant_repository
from restaurant_layers.adaptors import restaurant_event_repository


restaurant_repo = restaurant_repository.DynamoDbRepository()
restaurant_event_repo = restaurant_event_repository.DynamoDbRepository()
restaurant_service = service.RestaurantService(restaurant_repo=restaurant_repo,
                                               restaurant_event_repo=restaurant_event_repo)


@pytest.fixture
def create_restaurant_cmd():

    json_ = """{
        "restaurant_name": "skylark",
        "restaurant_address": {
            "street1": "1 Main Street",
            "street2": "Unit 99",
            "city": "Oakland",
            "state": "CA",
            "zip": "94611"
        },
        "menu_items": [
            {
                "menu_id": "000001",
                "menu_name": "Curry Rice",
                "price": {
                    "value": 800,
                    "currency": "JPY"
                }
            },
            {
                "menu_id": "000002",
                "menu_name": "Hamburger",
                "price": {
                    "value": 1000,
                    "currency": "JPY"
                }
            },
            {
                "menu_id": "000003",
                "menu_name": "Ramen",
                "price": {
                    "value": 700,
                    "currency": "JPY"
                }
            }
        ]
    }"""

    cmd = commands.CreateRestaurant.from_json(json_)
    return cmd


def test_create_restaurant(create_restaurant_cmd):
    restaurant_id_dict = restaurant_service.create_restaurant(create_restaurant_cmd)

    assert isinstance(restaurant_id_dict, dict)
    assert isinstance(restaurant_id_dict['restaurant_id'], int)


@pytest.fixture
def get_restaurant_cmd():
    json_ = """{
        "restaurant_id": 5
    }"""

    cmd = commands.GetRestaurant.from_json(json_)
    return cmd


def test_find_by_id(get_restaurant_cmd):
    restaurant: restaurant_model.Restaurant = restaurant_service.find_by_id(get_restaurant_cmd)

    assert isinstance(restaurant, restaurant_model.Restaurant)
