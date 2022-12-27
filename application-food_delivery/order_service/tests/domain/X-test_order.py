import decimal
import datetime
import pytest
# from ...function.domain import order_model  # Todo: ...は２階層上位
# from ...function.domain import domain_event
# from ...function.common import common


@pytest.fixture
def delivery_information_master():
    d = {
        'delivery_time': datetime.datetime(2022, 11, 7, 12, 47, 49, 681904),
        'delivery_address': {
            'street1': '9 Amazing View',
            'street2': 'Soi 8',
            'city': 'Oakland',
            'state': 'CA',
            'zip': '94612'
        }
    }
    return d


def test_delivery_information(delivery_information_master):
    d = delivery_information_master
    delivery_information = order_model.DeliveryInformation(**d)

    assert delivery_information is not None



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

"""
d = {'consumer_id': 1511300065921,
     'restaurant': {
         'name': 'Ajanta',
         'restaurant_id': 1,
         'adress': {
             'street1': '1 Main Street',
             'street2': 'Unit 99',
             'city': 'Oakland', 'state': 'CA',
             'zip': '94611'},
         'menu_items': [
             {
                 'id': '1',
                 'name': 'Chicken Vindaloo',
                 'price': {'value': decimal.Decimal('12.34'), 'currency': 'USD'}
             }
         ]
     },
     'delivery_information':
         {
             'delivery_time': datetime.datetime(2022, 11, 7, 12, 47, 49, 681904),
             'delivery_address': {
                 'street1': '9 Amazing View',
                 'street2': None,
                 'city': 'Oakland', 
                 'state': 'CA',
                 'zip': '94612'
             }
         },
     'order_line_items': [
        {
            'menu_id': '1',
            'menu_id': '1',
            'name': 'Chicken Vindaloo',
            'price': {'value': decimal.Decimal('12.34'), 'currency': 'USD'},
            'quantity': 5
        }
     ]
}
"""


def test_create_order_with_from_dict_to_dict():
    # Test from_dict() and to_dict()
    order = order_model.Order.from_dict(order_details_mother_dict)
    d = order.to_dict()

    assert order.order_state == order_model.OrderState.APPROVAL_PENDING
    assert order.order_state == order_model.OrderState(d.get('order_state'))
    assert order.order_line_items.line_items[0].restaurant_name == d.get('order_line_items')[0].get('name')
    assert order.lock_version == 1
    """
    d = {
        'order_id': '4e75ed1132be4e2e949943aa0b7e6a5f',
        'lick_version': 1, 
        'order_state': 2, 
        'order_line_items': [
            {
                'menu_id': '1', 
                'menu_id': '1', 
                'name': 'Chicken Vindaloo', 
                'price': {
                    'value': Decimal('12.34'), 
                    'currency': 'USD'
                }, 
                'quantity': 5
            }
        ], 
        'restaurant_id': None, 
        'payment_information': None, 
        'consumer_id': 1511300065921, 
        'delivery_information': {
            'delivery_time': '2022-11-30T05:00:30.001000Z', 
            'delivery_address': {'street1': '9 Amazing View', 'street2': None, 'city':'Oakland', 'state': 'CA', 'zip': '94612'}
        }
    }
    """


@pytest.fixture
def order_mother():
    order, events = order_model.Order.create_order_from_dict(order_details_mother_dict,
                                                             restaurant_mother_dict)
    return order, events


def test_create_order(order_mother: (order_model.Order, list[domain_event.OrderCreated])):
    # eventが正しいか？
    # order_stateが正しいか？
    order = order_mother[0]
    event = order_mother[1][0]

    assert order.order_state == order_model.OrderState.APPROVAL_PENDING
    assert order.lock_version == 1

    # OrderCreated Eventの検証データを作成
    line_item = order_model.OrderLineItem.from_dict(order_line_item_mother_dict)
    order_details = order_model.OrderDetails(
        consumer_id=order_details_mother_dict.get('consumer_id'),
        restaurant_id=order_details_mother_dict.get('restaurant_id'),
        line_items=order_model.OrderLineItems([line_item]),
        order_total=common.Money(decimal.Decimal('12.34'), 'USD') * 5
    )
    delivery_address = common.Address.from_dict(delivery_address_mother_dict)
    test_event = domain_event.OrderCreated(order_id=order.order_id,
                                           order_details=order_details,
                                           delivery_address=delivery_address,
                                           restaurant_name=restaurant_mother_dict.get('name'))

    assert event == test_event


def test_calculate_total(order_mother):
    order = order_mother[0]
    event = order_mother[1][0]

    value = menu_item_mother_dict.get('price').get('value')
    currency = menu_item_mother_dict.get('price').get('currency')
    quantity = order_line_item_mother_dict.get('quantity')
    assert order.get_order_total() == common.Money(value, currency) * quantity


def test_authorize(order_mother):
    order = order_mother[0]
    event = order_mother[1][0]

    events: list[domain_event.DomainEvent] = order.note_approved()

    assert [domain_event.OrderAuthorized(order_id=order.order_id)] == events


def test_revise_order(order_mother):
    """ Order Line Itemの変更 """
    order = order_mother[0]
    event = order_mother[1][0]

    # OrderState.APPROVAL_PENDING

    # Orderを受け付けた状態にする -> OrderState.APPROVAL_PENDING
    order.note_approved()

    # Order Line Itemの変更
    # Revisionの作成   quantityを5->10に変更
    revised_order_line_item = order_model.RevisedOrderLineItem(quantity=10, menu_id='1')
    order_revision = order_model.OrderRevision(delivery_information=None,
                                               revised_order_line_items=[revised_order_line_item])

    # 実際に変更はせず変更したときの金額を算出する -> OrderState.REVISION_PENDING
    change, events = order.revise(order_revision)
    # change: order_model.LineItemQuantityChange -> current_order_total, new_order_total, delta
    # events: domain_event.DomainEvent     order_revision, current_order_total, new_order_total

    # Line Item変更の金額のassert
    value = menu_item_mother_dict.get('price').get('value')
    currency = menu_item_mother_dict.get('price').get('currency')
    quantity = 10
    assert change.new_order_total == common.Money(value, currency) * quantity

    # 金額変更がOKであれば、実際にquantityの変更を実施する。-> OrderState.APPROVED
    order.confirm_revision(order_revision)

    # 変更された金額の確認
    assert order.get_order_total() == common.Money(value, currency) * quantity
