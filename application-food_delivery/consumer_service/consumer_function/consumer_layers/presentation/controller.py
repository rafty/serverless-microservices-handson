import re
import json
import traceback
from consumer_layers.common import common
from consumer_layers.common import exceptions
from consumer_layers.common import json_encoder
from consumer_layers.service import commands
from consumer_layers.service import handlers
from consumer_layers.adaptors import consumer_repository
from consumer_layers.adaptors import consumer_event_repository


CONSUMER_REPOSITORY = consumer_repository.DynamoDbRepository()
CONSUMER_EVENT_REPOSITORY = consumer_event_repository.DynamoDbRepository()
HANDLER = handlers.Handler(consumer_repo=CONSUMER_REPOSITORY,
                           consumer_event_repo=CONSUMER_EVENT_REPOSITORY)


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

        cmd = None
        if re.fullmatch('/consumers', path) and http_method == 'POST':
            """ POST /consumers  - Create Consumer
            http_method: POST
            path: "/consumers"
            path_parameters: None
            query_string_parameters: None
            body = Consumer Information JSON
            """
            cmd = commands.CreateConsumer.from_json(body_json=body_json)
        elif re.fullmatch('/consumers/[0-9]+', path) and http_method == 'GET':
            """ GET /consumers  - Get Consumer
            http_method: GET
            path: "/consumers/12345678"
            path_parameters: {"consumer_id": 12345678}
            query_string_parameters: None
            body: None
            """
            cmd = commands.GetConsumer(consumer_id=path_parameters.get('consumer_id'))
        else:
            raise exceptions.UnsupportedRoute(f'Unsupported Route :{http_method}')

        resp = HANDLER.commands_handler(cmd)
        resp_dict = resp.to_dict()

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
        traceback.print_exc()
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': str(e),
            })
        }

    except exceptions.UnsupportedRoute as e:
        print(str(e))
        traceback.print_exc()
        return {
            'statusCode': 405,
            'body': json.dumps({
                'message': str(e),
            })
        }

    except Exception as e:
        print(e)
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to perform operation.',
                'errorMsg': str(e),
            })
        }


# -------------------------------------------------
# from StepFunctions
# -------------------------------------------------

def stepfunctions_invocation(event: dict):
    """
    {
        "task_context": {
            "type": 1,
            "value": {
                "state_machine": "CreateOrderSaga",
                "action": "VALIDATE_CONSUMER"
            }
        },
        "order_details": {
            "consumer_id": 4,
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
        }
    }
    """
    try:
        print(f'stepfunctions_invocation(): event: {event}')
        state_machine = event['task_context']['value']['state_machine']
        action = event['task_context']['value']['action']

        cmd = None
        if state_machine == "CreateOrderSaga" and action == 'VALIDATE_CONSUMER':
            money_total = common.Money.from_dict(event['order_details']['order_total'])
            cmd = commands.ValidateOrderForConsumer(
                                        consumer_id=event['order_details']['consumer_id'],
                                        money_total=money_total)
        else:
            raise exceptions.InvalidSagaCmd(f'stepfunctions_invocation: '
                                            f'state_machine:{state_machine}, action:{action}')

        saga_resp = HANDLER.saga_commands_handler(cmd)
        return saga_resp

    except Exception as e:
        print(str(e))
        traceback.print_exc()
        raise e
