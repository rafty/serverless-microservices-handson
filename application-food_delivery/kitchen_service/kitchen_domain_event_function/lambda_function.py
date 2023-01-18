import os
import json
from json_encoder import JSONEncoder
import boto3
from boto3.dynamodb.types import TypeDeserializer
from aws_xray_sdk import core as x_ray

x_ray.patch_all()
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

    # python_obj['channel'] = python_obj['SK'].split('#')[1]
    # del python_obj['PK']
    # del python_obj['SK']
    # return python_obj

    # EventEnvelopの変換
    python_obj['aggregate'] = python_obj['PK'].split('#')[0]
    python_obj['aggregate_id'] = python_obj['PK'].split('#')[1]
    python_obj['event_type'] = python_obj['SK'].split('#')[1]
    python_obj['event_id'] = int(python_obj['SK'].split('#')[3])  # intに変換する
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
    print(f'event_publish() put_event.Detail: {json.dumps(record, cls=JSONEncoder)}')
    print(f'EventBridge put_events resp: {resp}')


def is_dynamo_insert(record):
    if record['eventName'] != 'INSERT':
        """INSERTでない"""
        return False
    return True


def is_kitchen_ticket_domain_event(record):
    if not record['dynamodb']['NewImage']['PK']['S'].startswith('TICKET#'):
        """KitchenTicketDomainEventでない!!"""
        return False
    return True


def event_handler(record):

    if not is_dynamo_insert(record):
        return
    if not is_kitchen_ticket_domain_event(record):
        return

    python_obj = convert_to_python_obj(record['dynamodb']['NewImage'])

    event_type = python_obj['event_type']
    if event_type == "TicketCreated":
        event_publish(python_obj)
    elif event_type == "TicketAccepted":
        event_publish(python_obj)
    elif event_type == "TicketCancelled":
        event_publish(python_obj)
    elif event_type == "TicketPreparationStarted":
        pass
    elif event_type == "TicketPreparationCompleted":
        pass
    elif event_type == "TicketPickedUp":
        pass
    elif event_type == "TicketRevised":
        pass
    else:
        raise UnsupportedEventChannelException(f'event_type:{event_type}')


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
