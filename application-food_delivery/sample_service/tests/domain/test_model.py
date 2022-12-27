from sample_layers.domain import model


def test_model():

    order = model.Order()

    assert order.name == 'Order'
