import os
import json
from json_encoder import JSONEncoder
import boto3
from boto3.dynamodb.types import TypeDeserializer

EVENTBUS_NAME = os.environ.get('EVENT_BUS_NAME')
EVENT_SOURCE = os.environ.get('EVENT_SOURCE')
EVENT_DETAIL_TYPE = os.environ.get('EVENT_DETAIL_TYPE')

eventbus = boto3.client('events')


class UnsupportedEventChannelException(Exception):
    pass


def convert_to_python_obj(dynamo_item) -> dict:
    deserializer = boto3.dynamodb.types.TypeDeserializer()
    python_obj = {k: deserializer.deserialize(v) for k, v in dynamo_item.items()}

    print(f'convert_to_python_obj()) python_obj: {json.dumps(python_obj, cls=JSONEncoder)}')

    python_obj['aggregate'] = python_obj['PK'].split('#')[0]
    # python_obj['channel'] = python_obj['SK'].split('#')[1]
    python_obj['event_type'] = python_obj['SK'].split('#')[1]

    del python_obj['PK']
    del python_obj['SK']
    """
    convert_to_python_obj()) python_obj: 
    {
        "event_id": 3,
        "restaurant_id": 31,
        "restaurant_address": {
            "zip": "94611",
            "city": "Oakland",
            "street1": "1 Main Street",
            "street2": "Unit 99",
            "state": "CA"
        },
        "SK": "EVENTTYPE#RestaurantCreated#EVENTID#3",
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
        "PK": "RESTAURANT#31",
        "restaurant_name": "skylark",
        "timestamp": "2022-12-28T09:19:51.664450Z"
    }
    """
    return python_obj


def dynamodb_streams_record_publish(record):
    dynamo_item = record['dynamodb']['NewImage']
    python_obj = convert_to_python_obj(dynamo_item)

    # publish to EventBridge
    resp = eventbus.put_events(
        Entries=[
            {
                'EventBusName': EVENTBUS_NAME,
                'Source': EVENT_SOURCE,
                'DetailType': EVENT_DETAIL_TYPE,
                'Detail': json.dumps(python_obj, cls=JSONEncoder),  # needs JSON
            }
        ],
    )

    print(f'put_event.Detail: {json.dumps(python_obj, cls=JSONEncoder)}')
    print(f'EventBridge put_events resp: {resp}')


def is_dynamo_insert(record):
    if record['eventName'] != 'INSERT':
        """INSERTでない"""
        return False
    return True


def is_restaurant_domain_event(record):
    if not record['dynamodb']['NewImage']['PK']['S'].startswith('RESTAURANT#'):
        """OrderDomainEventでない!!"""
        return False
    return True


def event_handler(record):

    if not is_dynamo_insert(record):
        return
    if not is_restaurant_domain_event(record):
        return

    dynamo_item = record['dynamodb']['NewImage']

    python_obj = convert_to_python_obj(dynamo_item)
    print(json.dumps(python_obj, cls=JSONEncoder))

    event_type = python_obj['event_type']
    if event_type == "RestaurantCreated":
        dynamodb_streams_record_publish(record)
    else:
        raise UnsupportedEventChannelException(f'event_type:{event_type}')


def lambda_handler(event, context):
    print(json.dumps(event))

    resp = None
    if event.get('Records', None):  # from SQS or DynamoDB Streams
        for record in event['Records']:
            if record['eventSource'] == 'aws:dynamodb':
                # dynamodb_streams_record_publish(record)
                event_handler(record)
            else:
                raise Exception(f"NotSupportEvent:{record['eventSource']}")
    elif event.get('detail-type', None):  # from event bridge  # Todo: delete
        # Event Bridge Invocation
        pass
    else:  # from api gateway  # Todo: delete
        pass

    return resp
