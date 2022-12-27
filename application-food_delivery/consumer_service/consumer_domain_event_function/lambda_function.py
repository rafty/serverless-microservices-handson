import os
import json
from json_encoder import JSONEncoder
import boto3
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError


eventbus = boto3.client('events')
# stepfunction = boto3.client('stepfunctions')


class UnsupportedEventChannelException(Exception):
    pass


def convert_to_python_obj(dynamo_item) -> dict:
    deserializer = boto3.dynamodb.types.TypeDeserializer()
    python_obj = {k: deserializer.deserialize(v) for k, v in dynamo_item.items()}

    # Primary Keyの変更: PK, SKをticket attributeに変換
    python_obj['channel'] = python_obj['SK'].split('#')[1]

    del python_obj['PK']
    del python_obj['SK']

    return python_obj


def event_handler(record):
    dynamo_item = record['dynamodb']['NewImage']
    python_obj = convert_to_python_obj(dynamo_item)
    print(json.dumps(python_obj, cls=JSONEncoder))
    channel = python_obj['channel']

    if channel == "ConsumerCreated":
        # Todo: EventBridgeにPublishする必要があるかどうか？
        #   event_publish()
        pass
    else:
        raise UnsupportedEventChannelException(f'channel:{channel}')


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
