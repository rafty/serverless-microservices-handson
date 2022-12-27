import re
import json
import traceback
from restaurant_layers.adaptors import restaurant_repository
from restaurant_layers.adaptors import restaurant_event_repository
from restaurant_layers.service import handlers
from restaurant_layers.service import commands
from restaurant_layers.common import exception
from restaurant_layers.common import json_encoder


# injection
RESTAURANT_REPOSITORY = restaurant_repository.DynamoDbRepository()
RESTAURANT_EVENT_REPOSITORY = restaurant_event_repository.DynamoDbRepository()


def rest_request(event):
    http_method = event.get('httpMethod')
    path = event.get('path')
    path_parameters = event.get('pathParameters')
    query_string_parameters = event.get('queryStringParameters')
    body_json = event.get('body', '{}')  # JSON
    return http_method, query_string_parameters, path, path_parameters, body_json


def rest_invocation(event: dict):
    try:
        http_method, query_string_parameters, path, path_parameters, body_json = rest_request(event)

        cmd = None
        # if path == '/restaurants':
        if re.fullmatch('/restaurants', path) and http_method == 'POST':
            """ POST /restaurants  - Create Restaurant
            http_method: POST
            path: "/restaurants"
            path_parameters: None
            query_string_parameters: None
            body = Restaurant JSON
            """
            cmd = commands.CreateRestaurant.from_json(body_json=body_json)
        elif re.fullmatch('/restaurants/[0-9]+', path) and http_method == 'GET':
            """ GET /restaurants  - Get Restaurant
            http_method: GET
            path: "/restaurants/9"
            path_parameters: {"restaurant_id": "9"}
            query_string_parameters: None
            body: None
            """
            cmd = commands.GetRestaurant(
                restaurant_id=path_parameters.get('restaurant_id'))
        else:
            raise exception.UnsupportedRoute(f'Unsupported Route :{http_method}')

        handler = handlers.Handler(restaurant_repo=RESTAURANT_REPOSITORY,
                                   restaurant_event_repo=RESTAURANT_EVENT_REPOSITORY)

        response = handler.commands_handler(cmd=cmd)
        response_dict = response.to_dict()

        rest_response = {
            'statusCode': 200,
            'body': json.dumps(  # bodyはJSON
                        {
                            'message': f'Successfully finished operation: {http_method}',
                            'body': response_dict,
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
        print(e)
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to perform operation.',
                'errorMsg': str(e),
            })
        }
