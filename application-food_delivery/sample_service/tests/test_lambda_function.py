import sys
from sample_service.sample_function import lambda_function


def test_lambda_handler():
    resp = lambda_function.lambda_handler({'event': 123}, {'context': 'foo_bar'})

    assert resp is True
