import pytest
from restaurant_service.restaurant_domain_event_function import lambda_function


@pytest.fixture
def dynamodb_stream_records():
    event = {
        "Records": [
            {
                "eventID": "b20a1a9a0631ab804d5d13b8caddb178",
                "eventName": "INSERT",
                "eventVersion": "1.1",
                "eventSource": "aws:dynamodb",
                "awsRegion": "ap-northeast-1",
                "dynamodb": {
                    "ApproximateCreationDateTime": 1669889817,
                    "Keys": {
                        "SK": {
                            "S": "CHANNEL#RestaurantCreated#EVENTID#2c1a2c8d82e24dc99dcef140cd661ee7"
                        },
                        "PK": {
                            "S": "RESTAURANT#16"
                        }
                    },
                    "NewImage": {
                        "event_id": {
                            "S": "2c1a2c8d82e24dc99dcef140cd661ee7"
                        },
                        "restaurant_id": {
                            "N": "16"
                        },
                        "restaurant_address": {
                            "M": {
                                "zip": {
                                    "S": "94611"
                                },
                                "city": {
                                    "S": "Oakland"
                                },
                                "street1": {
                                    "S": "1 Main Street"
                                },
                                "street2": {
                                    "S": "Unit 99"
                                },
                                "state": {
                                    "S": "CA"
                                }
                            }
                        },
                        "SK": {
                            "S": "CHANNEL#RestaurantCreated#EVENTID#2c1a2c8d82e24dc99dcef140cd661ee7"
                        },
                        "menu_items": {
                            "L": [
                                {
                                    "M": {
                                        "price": {
                                            "M": {
                                                "currency": {
                                                    "S": "JPY"
                                                },
                                                "value": {
                                                    "N": "800"
                                                }
                                            }
                                        },
                                        "menu_name": {
                                            "S": "Curry Rice"
                                        },
                                        "menu_id": {
                                            "S": "000001"
                                        }
                                    }
                                },
                                {
                                    "M": {
                                        "price": {
                                            "M": {
                                                "currency": {
                                                    "S": "JPY"
                                                },
                                                "value": {
                                                    "N": "1000"
                                                }
                                            }
                                        },
                                        "menu_name": {
                                            "S": "Hamburger"
                                        },
                                        "menu_id": {
                                            "S": "000002"
                                        }
                                    }
                                },
                                {
                                    "M": {
                                        "price": {
                                            "M": {
                                                "currency": {
                                                    "S": "JPY"
                                                },
                                                "value": {
                                                    "N": "700"
                                                }
                                            }
                                        },
                                        "menu_name": {
                                            "S": "Ramen"
                                        },
                                        "menu_id": {
                                            "S": "000003"
                                        }
                                    }
                                }
                            ]
                        },
                        "PK": {
                            "S": "RESTAURANT#16"
                        },
                        "restaurant_name": {
                            "S": "skylark"
                        }
                    },
                    "SequenceNumber": "7580000000000016039639809",
                    "SizeBytes": 537,
                    "StreamViewType": "NEW_IMAGE"
                },
                "eventSourceARN": "arn:aws:dynamodb:ap-northeast-1:123456789012:table/RestaurantEvent/stream/2022-11-30T10:29:55.261"
            }
        ]
    }
    return event


@pytest.fixture
def dynamo_stream_image_python_obj():
    d = {
        "PK": "RESTAURANT#16",
        "SK": "CHANNEL#RestaurantCreated#EVENTID#2c1a2c8d82e24dc99dcef140cd661ee7",
        "channel": "RestaurantCreated",
        "event_id": "2c1a2c8d82e24dc99dcef140cd661ee7",
        "restaurant_id": 16,
        "restaurant_name": "skylark",
        "restaurant_address": {
            "zip": "94611",
            "city": "Oakland",
            "street1": "1 Main Street",
            "street2": "Unit 99",
            "state": "CA"
        },
        "menu_items": [
            {
                "price": {
                    "currency": "JPY",
                    "value": 800
                },
                "menu_name": "Curry Rice",
                "menu_id": "000001"
            },
            {
                "price": {
                    "currency": "JPY",
                    "value": 1000
                },
                "menu_name": "Hamburger",
                "menu_id": "000002"
            },
            {
                "price": {
                    "currency": "JPY",
                    "value": 700
                },
                "menu_name": "Ramen",
                "menu_id": "000003"
            }
        ],
    }
    return d


def test_convert_to_python_obj(dynamodb_stream_records):

    d = lambda_function.convert_to_python_obj(
        dynamodb_stream_records['Records'][0]['dynamodb']['NewImage'])

    assert d['event_id'] == '2c1a2c8d82e24dc99dcef140cd661ee7'
    assert d['channel'] == 'RestaurantCreated'



