import re
import json
import traceback
from account_layers.common import common
from account_layers.common import exceptions
from account_layers.common import json_encoder
from account_layers.domain import account_model
from account_layers.service import commands
from account_layers.service import handlers
from account_layers.adaptors import account_repository
from account_layers.adaptors import account_event_repository


ACCOUNT_REPOSITORY = account_repository.DynamoDbRepository()
ACCOUNT_EVENT_REPOSITORY = account_event_repository.DynamoDbRepository()
HANDLER = handlers.Handler(account_repo=ACCOUNT_REPOSITORY,
                           account_event_repo=ACCOUNT_EVENT_REPOSITORY)


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
        if re.fullmatch('/accounts', path) and http_method == 'POST':
            """ POST /accounts  - Create Account
            http_method: POST
            path: "/accounts"
            path_parameters: None
            query_string_parameters: None
            body = Consumer Information JSON
            """
            cmd = commands.CreateAccount.from_json(body_json=body_json)
        elif re.fullmatch('/accounts', path) and http_method == 'GET':
            """ GET /accounts?consumer_id=1  - Get Account
            http_method: GET
            path: "/accounts"
            path_parameters: None
            query_string_parameters: consumer_id: 1
            body: None
            """
            # cmd = commands.GetAccount(account_id=path_parameters.get('account_id'))
            cmd = commands.GetAccount(consumer_id=query_string_parameters.get('consumer_id'))
        else:
            raise exceptions.UnsupportedRoute(f'Unsupported Route :{http_method}')

        resp = HANDLER.commands_handler(cmd)

        resp_ = None
        if isinstance(resp, account_model.Account):
            resp_ = resp.to_dict()

        if isinstance(resp, list):
            resp_ = [account.to_dict()
                     for account in resp if isinstance(resp, account_model.Account)]

        rest_response = {
            'statusCode': 200,
            'body': json.dumps(  # bodyはJSON
                        {
                            'message': f'Successfully finished operation: {http_method}',
                            'body': resp_,
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
                "action": "AUTHORIZE_CARD"
            }
        },
        "order_id":
        "consumer_id": 4,
        "order_total": {
                         "currency": "JPY",
                         "value": 5100
                       }
    }
    """
    try:
        print(f'stepfunctions_invocation(): event: {event}')
        state_machine = event['task_context']['value']['state_machine']
        action = event['task_context']['value']['action']

        cmd = None
        if state_machine == "CreateOrderSaga" and action == 'AUTHORIZE_CARD':
            money_total = common.Money.from_dict(event['order_total'])
            cmd = commands.AuthorizeCard(consumer_id=event['consumer_id'],
                                         money_total=money_total)

        elif state_machine == "CancelOrderSaga" and action == 'REVERSE_AUTHORIZE_CARD':
            money_total = common.Money.from_dict(event['order_total'])
            cmd = commands.ReverseAuthorizeCard(consumer_id=event['consumer_id'],
                                                order_id=event['order_id'],
                                                money_total=money_total)

        elif state_machine == "ReviseOrderSaga" and action == 'REVISE_AUTHORIZE_CARD':
            money_total = common.Money.from_dict(event['new_order_total'])
            cmd = commands.ReviseAuthorizeCard(consumer_id=event['consumer_id'],
                                               order_id=event['order_id'],
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
