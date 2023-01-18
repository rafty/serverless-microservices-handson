import decimal
import re
import json
import traceback
from delivery_layer.common import exception
from delivery_layer.common import json_encoder
from delivery_layer.service import commands
from delivery_layer.service import events
from delivery_layer.service import handlers
from delivery_layer.adaptors import restaurant_replica_repository
from delivery_layer.adaptors import delivery_repository
from delivery_layer.adaptors import delivery_event_repository
from delivery_layer.adaptors import courier_repository
from delivery_layer.domain import delivery_model


DELIVERY_REPOSITORY = delivery_repository.DynamoDbRepository()
DELIVERY_EVENT_REPOSITORY = delivery_event_repository.DynamoDbRepository()
COURIER_REPOSITORY = courier_repository.DynamoDbRepository()
RESTAURANT_REPLICA_REPOSITORY = restaurant_replica_repository.DynamoDbRepository()

HANDLER = handlers.Handler(delivery_repo=DELIVERY_REPOSITORY,
                           delivery_event_repo=DELIVERY_EVENT_REPOSITORY,
                           courier_repo=COURIER_REPOSITORY,
                           restaurant_repo=RESTAURANT_REPLICA_REPOSITORY)

# -------------------------------------------------
# Eventbus Invocation
# -------------------------------------------------


def extract_parameter_from_event(event):
    event_source = event.get('source', None)
    event_detail = event.get('detail', None)
    event_type = event.get('detail', None).get('event_type')
    return event_source, event_detail, event_type


def eventbus_invocation(event: dict):
    try:
        event_source, event_detail, event_type = extract_parameter_from_event(event)
        if event_source == 'com.restaurant.created' and event_type == 'RestaurantCreated':
            event_ = events.RestaurantCreated.from_event(event_detail)
            HANDLER.events_handler(event_)

        elif event_source == 'com.order.created' and event_type == 'OrderCreated':
            print(f'eventbus_invocation() OrderCreated')
            event_ = events.OrderCreated.from_event(event_detail)
            HANDLER.events_handler(event_)

        elif event_source == 'com.order.created' and event_type == 'OrderAuthorized':
            pass

        elif event_source == 'com.ticket.accepted' and event_type == 'TicketCreated':
            pass
            # event_ = events.TicketCreated.from_event(event_detail)
            # HANDLER.events_handler(event_)
            # 現在TicketCreatedはDeliveryで使用していない。

        elif event_source == 'com.ticket.accepted' and event_type == 'TicketAccepted':
            event_ = events.TicketAccepted.from_event(event_detail)
            HANDLER.events_handler(event_)

        elif event_source == 'com.ticket.accepted' and event_type == 'TicketCancelled':
            event_ = events.TicketCancelled.from_event(event_detail)
            HANDLER.events_handler(event_)

        else:
            raise Exception(f"NotSupportEvent: {event_source} : {event_type}")
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
        if re.fullmatch('/couriers/[0-9a-f]+/availability', path) and http_method == 'POST':
            d = json.loads(body_json, parse_float=decimal.Decimal)
            print(f'rest_invocation: courier availability: {d}')
            cmd = commands.CourierAvailability(courier_id=path_parameters.get('courier_id'),
                                               available=d['available'])
        # Todo ここから 2023.01.16
        elif re.fullmatch('/couriers/[0-9a-f]+/pickedup', path) and http_method == 'POST':
            d = json.loads(body_json, parse_float=decimal.Decimal)
            print(f'rest_invocation: courier pickedup: {d}')

            cmd = commands.CourierPickedUp(courier_id=path_parameters.get('courier_id'),
                                           delivery_id=d['delivery_id'])
        elif re.fullmatch('/couriers/[0-9a-f]+/delivered', path) and http_method == 'POST':
            d = json.loads(body_json, parse_float=decimal.Decimal)
            print(f'rest_invocation: courier delivered: {d}')

            cmd = commands.CourierDelivered(courier_id=path_parameters.get('courier_id'),
                                            delivery_id=d['delivery_id'])
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
