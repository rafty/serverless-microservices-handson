import decimal
import pytest
from delivery_layer.adaptors import restaurant_replica_repository
from delivery_layer.domain import restaurant_model


repo = restaurant_replica_repository.DynamoDbRepository()


def test_find_restaurant_by_id():

    restaurant = repo.find_by_id(restaurant_id=27)

    assert isinstance(restaurant, restaurant_model.Restaurant)
    assert restaurant.restaurant_id == 27

