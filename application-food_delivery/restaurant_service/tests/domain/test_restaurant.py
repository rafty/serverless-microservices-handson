import pytest
from restaurant_layers.domain import restaurant_model


@pytest.fixture
def restaurant_dict():
    d = {
        'restaurant_name': 'skylark',
        'restaurant_address': {
            'street1': '1 Main Street',
            'street2': 'Unit 99',
            'city': 'Oakland',
            'state': 'CA',
            'zip': '94611'
        },
        'menu_items': [
            {
                'menu_id': '000001',
                'menu_name': 'Curry Rice',
                'price': {
                    'value': 800,
                    'currency': 'JPY'
                }
            },
            {
                'menu_id': '000002',
                'menu_name': 'Hamburger',
                'price': {
                    'value': 1000,
                    'currency': 'JPY'
                }
            },
            {
                'menu_id': '000003',
                'menu_name': 'Ramen',
                'price': {
                    'value': 700,
                    'currency': 'JPY'
                }
            }
        ]
    }
    return d


def test_restaurant_from_dict(restaurant_dict):
    restaurant = restaurant_model.Restaurant.from_dict(restaurant_dict)

    assert restaurant.restaurant_name == 'skylark'

    restaurant_dict = restaurant.to_dict()

    assert restaurant_dict['restaurant_name'] == 'skylark'


def test_restaurant_create_from_dict(restaurant_dict):
    restaurant, events = restaurant_model.Restaurant.create_from_dict(restaurant_dict)

    assert restaurant.restaurant_name == 'skylark'
    assert events[0].restaurant_name == 'skylark'
