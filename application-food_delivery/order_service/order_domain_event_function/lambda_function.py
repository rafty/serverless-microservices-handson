import os
import json
from json_encoder import JSONEncoder
import boto3
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError

STATEMACHINE_ARN_FOR_CREATE_ORDER_SAGA = os.environ.get('STATEMACHINE_ARN_FOR_CREATE_ORDER_SAGA')
STATEMACHINE_ARN_FOR_CANCEL_ORDER_SAGA = os.environ.get('STATEMACHINE_ARN_FOR_CANCEL_ORDER_SAGA')
STATEMACHINE_ARN_FOR_REVISE_ORDER_SAGA = os.environ.get('STATEMACHINE_ARN_FOR_REVISE_ORDER_SAGA')

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
    # Todo: 元からあるので以下の処理を削除した。
    # python_obj['restaurant_id'] = int(python_obj['PK'].split('#')[1])
    # python_obj['event_id'] = python_obj['SK'].split('#')[3]

    del python_obj['PK']
    del python_obj['SK']

    return python_obj


def start_create_order_saga(record):
    input_json = json.dumps(record, cls=JSONEncoder)
    run_name = f"ORDER@{record['order_id']}@EVENTID@{record['event_id']}"
    # run_name must have length less than or equal to 80
    print(f'start_create_order_saga: name: {run_name}, input: {input_json}')

    # ------------------------
    # 注: run_nameがあることによりlambdaの再実行で、Stepfunctionのリトライが防げる
    # An error occurred (ExecutionAlreadyExists) when calling the StartExecution operation
    # ------------------------

    try:
        resp = stepfunction.start_execution(
            name=run_name,
            stateMachineArn=STATEMACHINE_ARN_FOR_CREATE_ORDER_SAGA,
            input=input_json
        )
        print(f"Start CreateOrderSaga: ARN:{resp['executionArn']}, name:{run_name}")

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code in ['ExecutionLimitExceeded',
                          'ExecutionAlreadyExists',
                          'InvalidArn',
                          'InvalidExecutionInput',
                          'InvalidName',
                          'StateMachineDoesNotExist',
                          'StateMachineDeleting',
                          'ValidationException']:
            print(e)
            raise e
        else:
            print(e)
            raise e

    except Exception as e:
        print(e)
        raise Exception


def start_cancel_order_saga(record):
    input_json = json.dumps(record, cls=JSONEncoder)
    run_name = f"ORDER@{record['order_id']}@EVENTID@{record['event_id']}"
    # run_name must have length less than or equal to 80

    print(f'start_cancel_order_saga: name: {run_name}, input: {input_json}')

    try:
        resp = stepfunction.start_execution(
            name=run_name,
            stateMachineArn=STATEMACHINE_ARN_FOR_CANCEL_ORDER_SAGA,
            input=input_json
        )
        print(f"Start CANCELOrderSaga: ARN:{resp['executionArn']}, name:{run_name}")

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code in ['ExecutionLimitExceeded',
                          'ExecutionAlreadyExists',
                          'InvalidArn',
                          'InvalidExecutionInput',
                          'InvalidName',
                          'StateMachineDoesNotExist',
                          'StateMachineDeleting',
                          'ValidationException']:
            print(e)
            raise e
        else:
            print(e)
            raise e

    except Exception as e:
        print(e)
        raise Exception


def start_revise_order_saga(record):
    input_json = json.dumps(record, cls=JSONEncoder)

    run_name = f"ORDER@{record['order_id']}@EVENTID@{record['event_id']}"
    # run_name must have length less than or equal to 80

    print(f'start_revise_order_saga: name: {run_name}, input: {input_json}')

    try:
        resp = stepfunction.start_execution(
            name=run_name,
            stateMachineArn=STATEMACHINE_ARN_FOR_REVISE_ORDER_SAGA,
            input=input_json
        )
        print(f"Start ReviseOrderSaga: ARN:{resp['executionArn']}, name:{run_name}")

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code in ['ExecutionLimitExceeded',
                          'ExecutionAlreadyExists',
                          'InvalidArn',
                          'InvalidExecutionInput',
                          'InvalidName',
                          'StateMachineDoesNotExist',
                          'StateMachineDeleting',
                          'ValidationException']:
            print(e)
            raise e
        else:
            print(e)
            raise e

    except Exception as e:
        print(e)
        raise Exception


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
    # print(json.dumps(python_obj, cls=JSONEncoder))
    channel = python_obj['channel']

    if channel == "OrderCreated":
        start_create_order_saga(python_obj)
        event_publish(python_obj)
    elif channel == "OrderAuthorized":
        pass
        # Todo: EventBridgeにPublishする必要があるかどうか？
    elif channel == "CancelOrderSagaRequested":
        start_cancel_order_saga(python_obj)
    elif channel == "OrderCancelled":
        pass
        # Todo: EventBridgeにPublishする必要があるかどうか？
    elif channel == "ReviseOrderSagaRequested":
        start_revise_order_saga(python_obj)
    elif channel == "OrderRevisionProposed":
        pass
        # Todo: EventBridgeにPublishする必要があるかどうか？

    elif channel == "OrderRevised":
        pass
        # Todo: EventBridgeにPublishする必要があるかどうか？

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
