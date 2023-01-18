import os
import json
from json_encoder import JSONEncoder
import boto3
from boto3.dynamodb.types import TypeDeserializer
from aws_xray_sdk import core as x_ray

x_ray.patch_all()
eventbus = boto3.client('events')


class UnsupportedEventChannelException(Exception):
    pass


def convert_to_python_obj(dynamo_item) -> dict:
    deserializer = boto3.dynamodb.types.TypeDeserializer()
    python_obj = {k: deserializer.deserialize(v) for k, v in dynamo_item.items()}

    # EventEnvelopの変換
    python_obj['aggregate'] = python_obj['PK'].split('#')[0]
    python_obj['aggregate_id'] = python_obj['PK'].split('#')[1]
    python_obj['event_type'] = python_obj['SK'].split('#')[1]
    python_obj['event_id'] = int(python_obj['SK'].split('#')[3])  # intに変換する
    del python_obj['PK']
    del python_obj['SK']

    return python_obj


def is_dynamo_insert(record):
    if record['eventName'] != 'INSERT':
        """INSERTでない"""
        return False
    return True


def is_consumer_domain_event(record):
    if not record['dynamodb']['NewImage']['PK']['S'].startswith('CONSUMER#'):
        """OrderDomainEventでない!!"""
        return False
    return True


def event_handler(record):

    if not is_dynamo_insert(record):
        return
    if not is_consumer_domain_event(record):
        return

    dynamo_item = record['dynamodb']['NewImage']

    python_obj = convert_to_python_obj(dynamo_item)
    print(json.dumps(python_obj, cls=JSONEncoder))

    event_type = python_obj['event_type']
    if event_type == "ConsumerCreated":
        # Todo: EventBridgeにPublishする必要があるかどうか？
        #   event_publish()
        pass
    else:
        raise UnsupportedEventChannelException(f'event_type:{event_type}')


def lambda_handler(event, context):
    print(json.dumps(event))

    resp = None
    if event.get('Records', None):  # from DynamoDB Streams
        for record in event['Records']:
            if record['eventSource'] == 'aws:dynamodb':
                event_handler(record)
            else:
                raise Exception(f"NotSupportEvent:{record['eventSource']}")
    else:
        raise Exception(f"NotSupportEvent: {event}")

    return resp
