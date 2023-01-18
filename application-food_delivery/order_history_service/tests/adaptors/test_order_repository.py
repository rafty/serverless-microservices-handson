import decimal
import pytest

from order_history_layers.store import order_repository
from order_history_layers.model import order_model


""" Restaurant for OrderCreated Event"""
menu_item_mother_dict = {
    'id': '1',
    'name': 'Chicken Vindaloo',
    'price': {
        'value': decimal.Decimal('12.34'),
        'currency': 'USD',
    },
}
restaurant_mother_dict = {
    'name': 'Ajanta',
    'restaurant_id': 1,
    'adress': {
        'street1': '1 Main Street',
        'street2': 'Unit 99',
        'city': 'Oakland',
        'state': 'CA',
        'zip': '94611',
    },
    'menu_items': [menu_item_mother_dict],
}

""" Delivery """
delivery_address_mother_dict = {
    'street1': '9 Amazing View',
    'street2': None,
    'city': 'Oakland',
    'state': 'CA',
    'zip': '94612',
}

delivery_information_mother_dict = {
    # 'delivery_time': datetime.datetime.now(),
    'delivery_time': "2022-11-30T05:00:30.001000Z",
    'delivery_address': delivery_address_mother_dict,
}


""" Order """
order_line_item_mother_dict = {
    'menu_id': menu_item_mother_dict['id'],
    'name': menu_item_mother_dict['name'],
    'price': menu_item_mother_dict['price'],
    'quantity': decimal.Decimal('5'),
}


order_details_mother_dict = {
    'consumer_id': decimal.Decimal('1511300065921'),
    'restaurant_id': decimal.Decimal('1'),
    'delivery_information': delivery_information_mother_dict,
    'order_line_items': [order_line_item_mother_dict]
}


@pytest.fixture
def order_mother():
    order, events = order_model.Order.create_order_from_dict(order_details_mother_dict,
                                                       restaurant_mother_dict)
    repo = order_repository.DynamoDbOrderRepository()
    repo.save(order)  # DynamoDBにsave()
    return order, events


def test_order_find_by_id(order_mother):
    order = order_mother[0]
    repo = order_repository.DynamoDbOrderRepository()

    fined_order = repo.find_by_id(order_id=order.order_id)

    assert isinstance(fined_order, order_model.Order)
    assert fined_order.order_id == order.order_id

