import os
import json
from json_encoder import JSONEncoder
import boto3
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError

EVENTBUS_NAME = os.environ.get('EVENT_BUS_NAME')
EVENT_SOURCE = os.environ.get('EVENT_SOURCE')
EVENT_DETAIL_TYPE = os.environ.get('EVENT_DETAIL_TYPE')

eventbus = boto3.client('events')
stepfunction = boto3.client('stepfunctions')


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


def event_publish(record):
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
    print(f'put_event.Detail: {json.dumps(record, cls=JSONEncoder)}')
    print(f'EventBridge put_events resp: {resp}')


def event_handler(record):

    if record['eventName'] != 'INSERT':
        return

    dynamo_item = record['dynamodb']['NewImage']
    python_obj = convert_to_python_obj(dynamo_item)
    channel = python_obj['channel']

    if channel == "TicketAccepted":
        event_publish(python_obj)
    elif channel == "TicketCreated":
        pass
    elif channel == "TicketCancelled":
        event_publish(python_obj)
    elif channel == "TicketPreparationStarted":
        pass
    elif channel == "TicketPreparationCompleted":
        pass
    elif channel == "TicketPickedUp":
        pass
    elif channel == "TicketRevised":
        pass
    else:
        raise UnsupportedEventChannelException(f'channel:{channel}')


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
