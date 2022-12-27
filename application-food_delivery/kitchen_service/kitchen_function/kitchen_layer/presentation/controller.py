import decimal
import re
import json
import datetime
import traceback
from kitchen_layer.common import exceptions
from kitchen_layer.common import json_encoder
from kitchen_layer.service import commands
from kitchen_layer.service import events
from kitchen_layer.service import handlers
from kitchen_layer.adaptors import restaurant_replica_repository
from kitchen_layer.adaptors import kitchen_repository
from kitchen_layer.adaptors import kitchen_event_repository
from kitchen_layer.domain import ticket_model

KITCHEN_REPOSITORY = kitchen_repository.DynamoDbRepository()
KITCHEN_EVENT_REPOSITORY = kitchen_event_repository.DynamoDbRepository()
RESTAURANT_REPLICA_REPOSITORY = restaurant_replica_repository.DynamoDbRepository()
HANDLER = handlers.Handler(kitchen_repo=KITCHEN_REPOSITORY,
                           kitchen_event_repo=KITCHEN_EVENT_REPOSITORY,
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
        traceback.print_exc()
        raise e


# -------------------------------------------------
# StepFunctions - Saga
# -------------------------------------------------

def stepfunctions_invocation(event: dict):
    print(f'stepfunctions_invocation(): event: {json.dumps(event)}')

    """
    {
        "task_context": {
            "type": 1,
            "value": {
                "state_machine": "CreateOrderSaga",
                "action": "CREATE_TICKET"
            }
        },
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
        "order_id": "b347f866e4dd484da4caeb1e4e7bff4a"
    }
    """
    try:
        state_machine = event['task_context']['value']['state_machine']
        action = event['task_context']['value']['action']

        cmd = None
        if state_machine == "CreateOrderSaga" and action == 'CREATE_TICKET':

            line_items = [
                ticket_model.TicketLineItem(quantity=item['quantity'],
                                            menu_id=item['menu_id'],
                                            name=item['name'])
                for item in event['order_line_items']
            ]
            cmd = commands.CreateTicket(ticket_id=event['order_id'],
                                        restaurant_id=event['restaurant_id'],
                                        line_items=line_items)

        elif state_machine == "CreateOrderSaga" and action == 'CONFIRM_CREATE_TICKET':
            # Create Order Saga
            cmd = commands.ConfirmCreateTicket(ticket_id=event['ticket_id'])

        elif state_machine == "CreateOrderSaga" and action == 'CANCEL_CREATE_TICKET':
            # Create Order Saga 補償トランザクション
            cmd = commands.CancelCreateTicket(ticket_id=event['ticket_id'])

        elif state_machine == "CancelOrderSaga" and action == 'BEGIN_CANCEL_TICKET':
            # Cancel Order Saga
            cmd = commands.BeginCancelTicket(ticket_id=event['order_id'])
            # 注意 order_idとticket_idは同じもの

        elif state_machine == "CancelOrderSaga" and action == 'CONFIRM_CANCEL_TICKET':
            # Cancel Order Saga
            cmd = commands.ConfirmCancelTicket(ticket_id=event['order_id'])
            # 注意 order_idとticket_idは同じもの

        elif state_machine == "CancelOrderSaga" and action == 'UNDO_BEGIN_CANCEL_TICKET':
            # Cancel Order Saga - 補償トランザクション
            cmd = commands.UndoBeginCancelTicket(ticket_id=event['order_id'])
            # 注意 order_idとticket_idは同じもの

        elif state_machine == "ReviseOrderSaga" and action == 'BEGIN_REVISE_TICKET':
            # Revise Order Saga
            cmd = commands.BeginReviseTicket(
                                     ticket_id=event['order_id'],
                                     revised_order_line_items=event['revised_order_line_items'])
            # 注意 order_idとticket_idは同じもの
        elif state_machine == "ReviseOrderSaga" and action == 'CONFIRM_REVISE_TICKET':
            # Revise Order Saga
            cmd = commands.ConfirmReviseTicket(
                                     ticket_id=event['order_id'],
                                     revised_order_line_items=event['revised_order_line_items'])
            # 注意 order_idとticket_idは同じもの
        elif state_machine == "ReviseOrderSaga" and action == 'UNDO_BEGIN_REVISE_TICKET':
            # Revise Order Saga
            cmd = commands.UndoBeginReviseTicket(ticket_id=event['order_id'])
            # 注意 order_idとticket_idは同じもの

        else:
            raise exceptions.InvalidSagaCmd(f'InvalidSagaCmd '
                                            f'state_machine:{state_machine}, action:{action}')

        saga_resp = HANDLER.saga_commands_handler(cmd)
        return saga_resp

    except Exception as e:
        print(str(e))
        traceback.print_exc()
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
    return http_method, query_string_parameters, path, path_parameters, body_json


def rest_invocation(event: dict):
    print(f'rest_invocation(): event: {event}')
    try:
        http_method, query_string_parameters, path, path_parameters, body_json \
            = rest_request(event)

        # path="/tickets/{ticketId}/accept" POST

        cmd = None
        if re.fullmatch('/tickets/[0-9a-f]+/accept', path) and http_method == 'POST':
            """ POST /tickets/ticket_id/accept  - Accept Ticket
            http_method: POST
            path: "/tickets/a477f597d28d172789f06886806bc55" # order_idとticket_idは同じもの
            path_parameters: {"ticket_id": 1}
            query_string_parameters: None
            body: {
                    "ready_by": "2022-11-30T05:00:30.001000Z"
                  }
            """
            d = json.loads(body_json, parse_float=decimal.Decimal)
            redy_by = datetime.datetime.strptime(d['ready_by'], '%Y-%m-%dT%H:%M:%S.%fZ')
            cmd = commands.AcceptTicket(ticket_id=path_parameters.get('ticket_id'),
                                        ready_by=redy_by)
        else:
            raise exceptions.UnsupportedRoute(f'Unsupported Route :{http_method}')

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

    except exceptions.InvalidName as e:
        print(str(e))
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': str(e),
            })
        }

    except exceptions.UnsupportedRoute as e:
        print(str(e))
        return {
            'statusCode': 405,
            'body': json.dumps({
                'message': str(e),
            })
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to perform operation.',
                'errorMsg': str(e),
            })
        }
