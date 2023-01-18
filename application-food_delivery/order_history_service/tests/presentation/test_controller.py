import decimal
import json
import pytest
from order_history_layers.presentation import controller


@pytest.fixture
def create_order_request():
    body_json = """
    {
    "restaurant_id": 1,
    "consumer_id": 2,
    "line_items": [
        {
            "menu_id": "000001",
            "quantity": 5
        },
        {
            "menu_id": "000002",
            "quantity": 3
        }
    ],
    "delivery_address": {
        "street1": "1 Main Street",
        "street2": "Unit 99",
        "city": "Oakland",
        "state": "CA",
        "zip": "94611"
    },
    "delivery_time": "2022-12-05T15:00:30.001000Z"
    }
    """
    # Todo: (注)delivery_address, delivery_timeはDomainでは、DeliveryInformationになる。

    request = {
        'httpMethod': 'POST',
        'path': '/orders',
        'pathParameters': None,
        'queryStringParameters': None,
        'body': body_json
    }
    return request


def test_create_order(create_order_request):

    rest_response = controller.rest_invocation(event=create_order_request)

    assert rest_response['statusCode'] == 200





# def test_presentation_create_order():
#     rest_response = controller.rest_invocation(event=lambda_event_with_create_order_request)
#     body_json = rest_response.get('body')
#     body_dict = json.loads(body_json, parse_float=decimal.Decimal, parse_int=decimal.Decimal)
#     body_in_body_dict = body_dict.get('body')
#
#     assert rest_response['statusCode'] == 200
#     assert isinstance(body_in_body_dict['order_id'], str)
#     assert body_in_body_dict['order_state'] == 2  # OrderState.APPROVAL_PENDING
#     assert body_in_body_dict['consumer_id'] == 1511300065921
#     assert body_in_body_dict['delivery_information']['delivery_time'] == "2022-11-30T05:00:30.001000Z"


