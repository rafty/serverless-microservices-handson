import pytest
from restaurant_layers.presentation import controller


@pytest.fixture
def create_restaurant_rest_request():
    body_json = """{
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
    request = {
        'path': '/restaurants',
        'httpMethod': 'POST',
        'queryStringParameters': None,
        'pathParameters': None,
        'body': body_json
    }
    return request


@pytest.fixture
def get_restaurant_rest_request():
    restaurant_id = 6
    request = {
        'httpMethod': 'GET',
        'path': '/restaurants',
        'pathParameters': {'restaurant_id': restaurant_id},
        'queryStringParameters': None,
        'body': None
    }
    return request


def test_create_restaurant_rest(create_restaurant_rest_request):
    rest_response = controller.rest_invocation(event=create_restaurant_rest_request)

    assert rest_response['statusCode'] == 200


def test_get_restaurant_rest(get_restaurant_rest_request):
    rest_response = controller.rest_invocation(event=get_restaurant_rest_request)

    assert rest_response['statusCode'] == 200
