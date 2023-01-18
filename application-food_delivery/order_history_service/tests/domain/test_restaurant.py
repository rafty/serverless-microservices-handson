import pytest
from order_history_layers.model import restaurant_model


@pytest.fixture
def restaurant_created_dict():
    d = {
            "restaurant_id": 1,
            "restaurant_name": "skylark",
            "menu_items": [
                {
                    "menu_id": "000001",
                    "menu_name": "Curry Rice",
                    "price": {
                        'value': 800,
                        'currency': 'JPY'
                    }
                },
                {
                    "menu_id": "000002",
                    "menu_name": "Hamburger",
                    "price": {
                        'value': 1000,
                        'currency': 'JPY'
                    }
                },
                {
                    "menu_id": "000003",
                    "menu_name": "Ramen",
                    "price": {
                        'value': 700,
                        'currency': 'JPY'
                    }
                }
            ]
        }
    return d


def test_restaurant_from_dict_to_dict(restaurant_created_dict):
    restaurant = restaurant_model.Restaurant.from_dict(restaurant_created_dict)

    assert restaurant.restaurant_id == 1

    d = restaurant.to_dict()

    assert d['restaurant_id'] == restaurant_created_dict['restaurant_id']


def test_find_menu_item(restaurant_created_dict):
    restaurant = restaurant_model.Restaurant.from_dict(restaurant_created_dict)
    menu = restaurant.find_menu_item(menu_id='000002')

    assert menu.menu_name == 'Hamburger'

    with pytest.raises(Exception) as e:
        no_menu = restaurant.find_menu_item(menu_id='000000')

    assert str(e.value) == 'MenuItemNotFound: 000000'


