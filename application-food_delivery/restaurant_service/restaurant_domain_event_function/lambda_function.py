import os
import json
from json_encoder import JSONEncoder
import boto3
from boto3.dynamodb.types import TypeDeserializer

EVENTBUS_NAME = os.environ.get('EVENT_BUS_NAME')
EVENT_SOURCE = os.environ.get('EVENT_SOURCE')
EVENT_DETAIL_TYPE = os.environ.get('EVENT_DETAIL_TYPE')

eventbus = boto3.client('events')


def convert_to_python_obj(dynamo_item) -> dict:
    deserializer = boto3.dynamodb.types.TypeDeserializer()
    python_obj = {k: deserializer.deserialize(v) for k, v in dynamo_item.items()}

    # Primary Keyの変更: PK, SKをticket attributeに変換
    python_obj['channel'] = python_obj['SK'].split('#')[1]
    # Todo: 元からあるので以下の処理を削除した。
    # python_obj['restaurant_id'] = int(python_obj['PK'].split('#')[1])
    # python_obj['event_id'] = python_obj['SK'].split('#')[3]

    del python_obj['PK']
    del python_obj['SK']

    """
    {
        "event_id": "2c1a2c8d82e24dc99dcef140cd661ee7",
        "restaurant_id": 16,
        "restaurant_address": {
            "zip": "94611",
            "city": "Oakland",
            "street1": "1 Main Street",
            "street2": "Unit 99",
            "state": "CA"
        },
        "SK": "CHANNEL#RestaurantCreated#EVENTID#2c1a2c8d82e24dc99dcef140cd661ee7",
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
        "PK": "RESTAURANT#16",
        "restaurant_name": "skylark",
        "channel": "RestaurantCreated"
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


def lambda_handler(event, context):
    print(json.dumps(event))

    resp = None
    if event.get('Records', None):  # from SQS or DynamoDB Streams
        for record in event['Records']:
            if record['eventSource'] == 'aws:dynamodb':
                dynamodb_streams_record_publish(record)
            elif record['eventSource'] == 'aws:sqs':  # Todo: delete
                # sqs_invocation(event)
                # 今回はない
                pass
            else:
                raise Exception(f"NotSupportEvent:{record['eventSource']}")
    elif event.get('detail-type', None):  # from event bridge  # Todo: delete
        # Event Bridge Invocation
        pass
    else:  # from api gateway  # Todo: delete
        pass

    return resp
