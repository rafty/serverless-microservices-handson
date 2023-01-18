import os
import json
from json_encoder import JSONEncoder
import boto3
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError
from aws_xray_sdk import core as x_ray

x_ray.patch_all()
EVENTBUS_NAME = os.environ.get('EVENT_BUS_NAME')
EVENT_SOURCE = os.environ.get('EVENT_SOURCE')
EVENT_DETAIL_TYPE = os.environ.get('EVENT_DETAIL_TYPE')

eventbus = boto3.client('events')


class UnsupportedEventTypeException(Exception):
    pass


def convert_to_python_obj(dynamo_item) -> dict:
    deserializer = boto3.dynamodb.types.TypeDeserializer()
    python_obj = {k: deserializer.deserialize(v) for k, v in dynamo_item.items()}

    print(f'convert_to_python_obj() python_obj: {python_obj}')

    # EventEnvelopの変換
    python_obj['aggregate'] = python_obj['PK'].split('#')[0]
    python_obj['aggregate_id'] = python_obj['PK'].split('#')[1]
    python_obj['event_type'] = python_obj['SK'].split('#')[1]
    python_obj['event_id'] = int(python_obj['SK'].split('#')[3])  # intに変換する
    del python_obj['PK']
    del python_obj['SK']

    return python_obj


def event_publish(record):

    print(f'put_event.Detail: {json.dumps(record, cls=JSONEncoder)}')

    # publish to EventBridge
    resp = eventbus.put_events(
        Entries=[
            {
                'EventBusName': EVENTBUS_NAME,
                'Source': EVENT_SOURCE,
                'DetailType': EVENT_DETAIL_TYPE,
                'Detail': json.dumps(record, cls=JSONEncoder),  # needs JSON
            }
        ],
    )
    print(f'EventBridge put_events resp: {resp}')


def is_dynamo_insert(record):
    if record['eventName'] != 'INSERT':
        """INSERTでない"""
        return False
    return True


def is_delivery_domain_event(record):
    if not record['dynamodb']['NewImage']['PK']['S'].startswith('DELIVERY#'):
        """DeliveryDomainEventでない!!"""
        return False
    return True


def event_handler(record):
    if not is_dynamo_insert(record):
        return
    if not is_delivery_domain_event(record):
        return

    item_dict = convert_to_python_obj(record['dynamodb']['NewImage'])

    event_type = item_dict['event_type']
    if event_type == "DeliveryPickedup":
        event_publish(item_dict)
    elif event_type == "DeliveryDelivered":
        event_publish(item_dict)
    else:
        raise UnsupportedEventTypeException(f'event_type:{event_type}')


def lambda_handler(event, context):
    print(f'event: {json.dumps(event)}')

    resp = None
    if event.get('Records', None):  # from SQS or DynamoDB Streams
        for record in event['Records']:
            if record['eventSource'] == 'aws:dynamodb':
                event_handler(record)
            else:
                raise Exception(f"NotSupportEvent:{record['eventSource']}")
    else:
        raise Exception(f"NotSupportEvent: {event}")

    return resp
