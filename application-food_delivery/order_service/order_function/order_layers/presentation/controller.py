import decimal
import re
import json
import traceback
from order_layers.common import exception
from order_layers.common import json_encoder
from order_layers.service import commands
from order_layers.service import events
from order_layers.service import handlers
from order_layers.adaptors import restaurant_replica_repository
from order_layers.adaptors import order_repository
from order_layers.adaptors import order_event_repository
from order_layers.domain import order_model

ORDER_REPOSITORY = order_repository.DynamoDbRepository()
ORDER_EVENT_REPOSITORY = order_event_repository.DynamoDbRepository()
RESTAURANT_REPLICA_REPOSITORY = restaurant_replica_repository.DynamoDbRepository()
HANDLER = handlers.Handler(order_repo=ORDER_REPOSITORY,
                           order_event_repo=ORDER_EVENT_REPOSITORY,
                           restaurant_replica_repo=RESTAURANT_REPLICA_REPOSITORY)

# -------------------------------------------------
# Eventbus Invocation
# -------------------------------------------------


def extract_parameter_from_event(event):
    event_source = event.get('source', None)
    event_detail = event.get('detail', None)
    channel = event.get('detail', None).get('channel')
    return event_source, event_detail, channel


def eventbus_invocation(event: dict):
    try:
        event_source, event_detail, channel = extract_parameter_from_event(event)
        if event_source == 'com.restaurant.created' and channel == 'RestaurantCreated':
            event_ = events.RestaurantCreated.from_event(event_detail)
            HANDLER.events_handler(event_)
        else:
            raise Exception(f"NotSupportEvent: {event_source} : {channel}")
        return None

    except Exception as e:
        raise e


# -------------------------------------------------
# REST API
# -------------------------------------------------

def rest_request(event):
    http_method = event.get('httpMethod')
    path = event.get('path')
    path_parameters = event.get('pathParameters')
    query_string_parameters = event.get('queryStringParameters')
    body_json = event.get('body', '{}')  # JSON

    print(f'http_method: {http_method}')
    print(f'query_string_parameters: {query_string_parameters}')
    print(f'path: {path}')
    print(f'path_parameters: {path_parameters}')
    print(f'body_json: {body_json}')

    return http_method, query_string_parameters, path, path_parameters, body_json


def rest_invocation(event: dict):
    try:
        http_method, query_string_parameters, path, path_parameters, body_json \
            = rest_request(event)

        cmd = None
        if re.fullmatch('/orders', path) and http_method == 'POST':
            """
            - Create Order
            POST /orders
            http_method: POST
            path: "/orders"
            path_parameters: None
            query_string_parameters: None
            body = Order Information JSON
            """
            """
            body JSON sample
            {
                "consumer_id": 4,
                "restaurant_id": 1,
                "delivery_information": {
                   "delivery_time": "2022-11-30T05:00:30.001000Z",
                   "delivery_address": {
                        "street1": "9 Amazing View",
                        "street2": "Soi 8",
                        "city": "Oakland",
                        "state": "CA",
                        "zip": "94612"
                    }
                },
                "order_line_items": [
                    {
                        "menu_id": "000001",
                        "quantity": 3
                    },
                    {
                        "menu_id": "000002",
                        "quantity": 2
                    },
                    {
                        "menu_id": "000003",
                        "quantity": 1
                    }
                ]
            }
            """
            cmd = commands.CreateOrder.from_json(body_json=body_json)

        elif re.fullmatch('/orders/[0-9a-f]+', path) and http_method == 'GET':  # uuid
            """
            - Get Order 
            GET /orders/xxxxxx
            http_method: GET
            path: "/orders/dc83abae951c4185ab3780a5b7c5f055"
            path_parameters: {"order_id": "dc83abae951c4185ab3780a5b7c5f055"}
            query_string_parameters: None
            body: None
            """
            cmd = commands.GetOrder(order_id=path_parameters.get('order_id'))

        elif re.fullmatch('/orders/[0-9a-f]+/cancel', path) and http_method == 'POST':
            """
            - Cancel Order
            POST /orders/dc83abae951c4185ab3780a5b7c5f055/cancel
            http_method: POST
            path: "/orders/dc83abae951c4185ab3780a5b7c5f055/cancel"
            path_parameters: {"order_id": "dc83abae951c4185ab3780a5b7c5f055"}
            query_string_parameters: None
            body None 
            """
            # cmd = commands.CancelOrder.from_json(body_json=body_json)  # いまここ
            cmd = commands.CancelOrder(order_id=path_parameters.get('order_id'))

        elif re.fullmatch('/orders/[0-9a-f]+/revise', path) and http_method == 'POST':
            """
            - Revise Order
            POST /orders/dc83abae951c4185ab3780a5b7c5f055/revise
            http_method: POST
            path: "/orders/dc83abae951c4185ab3780a5b7c5f055/revise"
            path_parameters: {"order_id": "dc83abae951c4185ab3780a5b7c5f055"}
            query_string_parameters: None
            body = Order Information JSON
            """
            """
            # body_json
            {
                "delivery_information": {
                   "delivery_time": "2022-11-30T05:00:30.001000Z",
                   "delivery_address": {
                        "street1": "9 Amazing View",
                        "street2": "Soi 8",
                        "city": "Oakland",
                        "state": "CA",
                        "zip": "94612"
                    }
                },
                "revised_order_line_items": [  
                    {                           # RevisedOrderLineItem
                        "menu_id": "000001",
                        "quantity": 3
                    },
                    {                           # RevisedOrderLineItem
                        "menu_id": "000002",
                        "quantity": 2
                    },
                    {                           # RevisedOrderLineItem
                        "menu_id": "000003",
                        "quantity": 1
                    }
                ]
            }
            """

            d = json.loads(body_json, parse_float=decimal.Decimal)
            delivery_information = order_model.DeliveryInformation.from_dict(
                                                                d['delivery_information'])
            revised_order_line_items = [order_model.RevisedOrderLineItem.from_dict(item)
                                        for item in d['revised_order_line_items']]
            order_revision = order_model.OrderRevision(
                                            delivery_information=delivery_information,
                                            revised_order_line_items=revised_order_line_items)
            cmd = commands.ReviseOrder(order_id=path_parameters.get('order_id'),
                                       order_revision=order_revision)

        else:
            raise exception.UnsupportedRoute(f'Unsupported Route :{http_method}')

        resp = HANDLER.commands_handler(cmd)

        resp_dict = resp.to_dict() if hasattr(resp, 'to_dict') else resp

        rest_response = {
            'statusCode': 200,
            'body': json.dumps(  # bodyはJSON
                        {
                            'message': f'Successfully finished operation: {http_method}',
                            'body': resp_dict,
                        },
                        cls=json_encoder.JSONEncoder
                    )
        }
        print(f'return response: {rest_response}')
        return rest_response

    except exception.InvalidName as e:
        print(str(e))
        traceback.print_exc()
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': str(e),
            })
        }

    except exception.UnsupportedRoute as e:
        print(str(e))
        traceback.print_exc()
        return {
            'statusCode': 405,
            'body': json.dumps({
                'message': str(e),
            })
        }

    except Exception as e:
        print(str(e))
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to perform operation.',
                'errorMsg': str(e),
            })
        }


# -------------------------------------------------
# StepFunctions - Saga
# -------------------------------------------------

def stepfunctions_invocation(event: dict):
    print(f'stepfunctions_invocation(): event: {event}')
    """
    {
        "task_context": {
            "type": 1,
            "value": {
                "state_machine": "OrderCreateSaga",
                "action": "APPROVE_ORDER"
            }
        },
        "input": {
            "event_id": "7d9210f8b4c9438d84a51740b12c2635",
            "delivery_information": {
                "delivery_address": {
                    "zip": "94612",
                    "city": "Oakland",
                    "street1": "9 Amazing View",
                    "street2": "Soi 8",
                    "state": "CA"
                },
                "delivery_time": "2022-11-30T05:00:30.001000Z"
            },
            "order_details": {
                "consumer_id": 1511300065921,
                "restaurant_id": 1,
                "order_line_items": [
                    {
                        "quantity": 3,
                        "price": {
                            "currency": "JPY",
                            "value": 800
                        },
                        "name": "Curry Rice",
                        "menu_id": "000001"
                    },
                    {
                        "quantity": 2,
                        "price": {
                            "currency": "JPY",
                            "value": 1000
                        },
                        "name": "Hamburger",
                        "menu_id": "000002"
                    },
                    {
                        "quantity": 1,
                        "price": {
                            "currency": "JPY",
                            "value": 700
                        },
                        "name": "Ramen",
                        "menu_id": "000003"
                    }
                ],
                "order_total": {
                    "currency": "JPY",
                    "value": 5100
                }
            },
            "order_id": "04516f76f6b0456d9e9916d667777890",
            "channel": "OrderCreated",
            "event_context": {
                "source": "stepfunctions",
                "state_machine": "CreateOrderSaga"
            }
        }
    }
    """
    try:
        state_machine = event['task_context']['value']['state_machine']
        action = event['task_context']['value']['action']

        cmd = None
        # ------------------------------------------------------------------
        # Create Order Saga
        # ------------------------------------------------------------------
        if state_machine == "CreateOrderSaga" and action == 'APPROVE_ORDER':
            cmd = commands.ApproveOrder(order_id=event['order_id'])
        elif state_machine == "CreateOrderSaga" and action == 'REJECT_ORDER':
            # 補償トランザクション
            cmd = commands.RejectOrder(order_id=event['order_id'])

        # ------------------------------------------------------------------
        # Cancel Order Saga
        # ------------------------------------------------------------------
        elif state_machine == "CancelOrderSaga" and action == 'BEGIN_CANCEL_ORDER':
            cmd = commands.BeginCancelOrder(order_id=event['order_id'])
        elif state_machine == "CancelOrderSaga" and action == 'UNDO_BEGIN_CANCEL_ORDER':
            # 補償トランザクション
            cmd = commands.UndoBeginCancelOrder(order_id=event['order_id'])
        elif state_machine == "CancelOrderSaga" and action == 'CONFIRM_CANCEL_ORDER':
            cmd = commands.ConfirmCancelOrder(order_id=event['order_id'])
        # ------------------------------------------------------------------
        # Revise Order Saga
        # ------------------------------------------------------------------
        elif state_machine == "ReviseOrderSaga" and action == 'BEGIN_REVISE_ORDER':
            order_revision = order_model.OrderRevision.from_dict(event['order_revision'])
            cmd = commands.BeginReviseOrder(order_id=event['order_id'],
                                            order_revision=order_revision)

        elif state_machine == "ReviseOrderSaga" and action == 'CONFIRM_REVISE_ORDER':
            order_revision = order_model.OrderRevision.from_dict(event['order_revision'])
            cmd = commands.ConfirmReviseOrder(order_id=event['order_id'],
                                              order_revision=order_revision)

        elif state_machine == "ReviseOrderSaga" and action == 'UNDO_BEGIN_REVISE_ORDER':
            cmd = commands.UndoBeginReviseOrder(order_id=event['order_id'])

        else:
            raise exception.InvalidSagaCmd(f'state_machine:{state_machine}, action:{action}')

        saga_resp = HANDLER.saga_commands_handler(cmd)

        resp_dict = saga_resp.to_dict() if hasattr(saga_resp, 'to_dict') else saga_resp
        return resp_dict

    except Exception as e:
        print(str(e))
        traceback.print_exc()
        raise e
