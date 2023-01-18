import decimal
import re
import json
import traceback
from order_history_layers.common import exceptions
from order_history_layers.common import json_encoder
from order_history_layers.service import commands
from order_history_layers.service import events
from order_history_layers.service import handlers
from order_history_layers.store import order_history_dao
from order_history_layers.model import order_history_model

ORDER_HISTORY_DAO = order_history_dao.DynamoDbDao()
HANDLER = handlers.Handler(order_history_dao=ORDER_HISTORY_DAO)

# -------------------------------------------------
# Eventbus Invocation
# -------------------------------------------------


def extract_parameter_from_event(event):
    event_source = event.get('source', None)
    event_detail = event.get('detail', None)
    event_type = event.get('detail', None).get('event_type')
    return event_source, event_detail, event_type


def eventbus_invocation(event: dict):
    """
    {
        "version": "0",
        "id": "8681fda7-862b-2bd9-b67c-bfa2b1b97bf4",
        "detail-type": "OrderCreated",
        "source": "com.order.created",
        "account": "338456725408",
        "time": "2023-01-10T07:38:40Z",
        "region": "ap-northeast-1",
        "resources": [],
        "detail": {
            "event_id": "39",
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
                "consumer_id": 4,
                "restaurant_id": 27,
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
            "order_id": "710f11c1574d49558a339f562f7135d6",
            "timestamp": "2023-01-10T07:38:38.511615Z",
            "aggregate": "ORDER",
            "aggregate_id": "710f11c1574d49558a339f562f7135d6",
            "event_type": "OrderCreated"
        }
    }
    """
    try:
        print(f'eventbus_invocation() event: {json.dumps(event, cls=json_encoder.JSONEncoder)}')

        event_source, event_detail, event_type = extract_parameter_from_event(event)

        if event_source == 'com.order.created' and event_type == 'OrderCreated':
            event_ = events.OrderCreated.from_event(event_detail)
            HANDLER.events_handler(event_)
        elif event_source == 'com.order.created' and event_type == 'OrderAuthorized':
            event_ = events.OrderAuthorized.from_event(event_detail)
            HANDLER.events_handler(event_)
        elif event_source == 'com.order.created' and event_type == 'OrderRejected':
            event_ = events.OrderRejected.from_event(event_detail)
            HANDLER.events_handler(event_)
        elif event_source == 'com.order.created' and event_type == 'OrderCancelled':
            event_ = events.OrderCancelled.from_event(event_detail)
            HANDLER.events_handler(event_)
        elif event_source == 'com.delivery.created' and event_type == 'DeliveryPickedup':
            event_ = events.DeliveryPickedup.from_event(event_detail)
            HANDLER.events_handler(event_)
        elif event_source == 'com.delivery.created' and event_type == 'DeliveryDelivered':
            event_ = events.DeliveryDelivered.from_event(event_detail)
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
        if re.fullmatch('/orders/', path) and http_method == 'GET':
            """
            - Get Order History
            POST /orders
            http_method: GET
            path: "/orders"
            path_parameters: None
            query_string_parameters: None
            body: None
            """
            # Todo:
            #  consumer_idは"Lambda Authorizer"で設定し、
            #  REST API Lambdaではevent.requestContext.authorizer.key を呼び出して取得する
            #  [API Gateway Lambda オーソライザーを使用する]
            #  https://docs.aws.amazon.com/ja_jp/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
            #  [Amazon API Gateway Lambda オーソライザーからの出力]
            #  https://docs.aws.amazon.com/ja_jp/apigateway/latest/developerguide/api-gateway-lambda-authorizer-output.html
            dummy_request_context = {
                'requestContext': {
                    'authorizer': {
                        'consumer_id': 4
                    }
                }
            }
            consumer_id = dummy_request_context.get('requestContext').get('authorizer').get('consumer_id')
            cmd = commands.GetOrders(consumer_id=consumer_id)

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
            """
            {
                "resource": "/orders/{order_id}",
                "path": "/orders/4824a7e36cd042c79192e3a4a2641ea1",
                "httpMethod": "GET",
                "headers": {
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate, br",
                    "CloudFront-Forwarded-Proto": "https",
                    "CloudFront-Is-Desktop-Viewer": "true",
                    "CloudFront-Is-Mobile-Viewer": "false",
                    "CloudFront-Is-SmartTV-Viewer": "false",
                    "CloudFront-Is-Tablet-Viewer": "false",
                    "CloudFront-Viewer-ASN": "17676",
                    "CloudFront-Viewer-Country": "JP",
                    "Host": "qnieunod45.execute-api.ap-northeast-1.amazonaws.com",
                    "Postman-Token": "f6e621f7-1475-47fc-8bb9-398068c37ee2",
                    "User-Agent": "PostmanRuntime/7.29.2",
                    "Via": "1.1 28cc684478478d9f9a85bebbb1ed4154.cloudfront.net (CloudFront)",
                    "X-Amz-Cf-Id": "l0JjQBHErviZ3OqmDc1hp_4-qm-9fCwfVQ9_W7ysfmC0bdnojiHMnw==",
                    "X-Amzn-Trace-Id": "Root=1-63c7bc96-379cb58d7705d4474e8eb758",
                    "X-Forwarded-For": "60.116.89.182, 130.176.189.234",
                    "X-Forwarded-Port": "443",
                    "X-Forwarded-Proto": "https"
                },
                "multiValueHeaders": {
                    "Accept": [
                        "*/*"
                    ],
                    "Accept-Encoding": [
                        "gzip, deflate, br"
                    ],
                    "CloudFront-Forwarded-Proto": [
                        "https"
                    ],
                    "CloudFront-Is-Desktop-Viewer": [
                        "true"
                    ],
                    "CloudFront-Is-Mobile-Viewer": [
                        "false"
                    ],
                    "CloudFront-Is-SmartTV-Viewer": [
                        "false"
                    ],
                    "CloudFront-Is-Tablet-Viewer": [
                        "false"
                    ],
                    "CloudFront-Viewer-ASN": [
                        "17676"
                    ],
                    "CloudFront-Viewer-Country": [
                        "JP"
                    ],
                    "Host": [
                        "qnieunod45.execute-api.ap-northeast-1.amazonaws.com"
                    ],
                    "Postman-Token": [
                        "f6e621f7-1475-47fc-8bb9-398068c37ee2"
                    ],
                    "User-Agent": [
                        "PostmanRuntime/7.29.2"
                    ],
                    "Via": [
                        "1.1 28cc684478478d9f9a85bebbb1ed4154.cloudfront.net (CloudFront)"
                    ],
                    "X-Amz-Cf-Id": [
                        "l0JjQBHErviZ3OqmDc1hp_4-qm-9fCwfVQ9_W7ysfmC0bdnojiHMnw=="
                    ],
                    "X-Amzn-Trace-Id": [
                        "Root=1-63c7bc96-379cb58d7705d4474e8eb758"
                    ],
                    "X-Forwarded-For": [
                        "60.116.89.182, 130.176.189.234"
                    ],
                    "X-Forwarded-Port": [
                        "443"
                    ],
                    "X-Forwarded-Proto": [
                        "https"
                    ]
                },
                "queryStringParameters": null,
                "multiValueQueryStringParameters": null,
                "pathParameters": {
                    "order_id": "4824a7e36cd042c79192e3a4a2641ea1"
                },
                "stageVariables": null,
                "requestContext": {
                    "resourceId": "ajck76",
                    "resourcePath": "/orders/{order_id}",
                    "httpMethod": "GET",
                    "extendedRequestId": "e7pnnG1lNjMFcGg=",
                    "requestTime": "18/Jan/2023:09:32:06 +0000",
                    "path": "/prod/orders/4824a7e36cd042c79192e3a4a2641ea1",
                    "accountId": "338456725408",
                    "protocol": "HTTP/1.1",
                    "stage": "prod",
                    "domainPrefix": "qnieunod45",
                    "requestTimeEpoch": 1674034326903,
                    "requestId": "1379e16b-a808-4e93-bf26-c3b37178a5c9",
                    "identity": {
                        "cognitoIdentityPoolId": null,
                        "accountId": null,
                        "cognitoIdentityId": null,
                        "caller": null,
                        "sourceIp": "60.116.89.182",
                        "principalOrgId": null,
                        "accessKey": null,
                        "cognitoAuthenticationType": null,
                        "cognitoAuthenticationProvider": null,
                        "userArn": null,
                        "userAgent": "PostmanRuntime/7.29.2",
                        "user": null
                    },
                    "domainName": "qnieunod45.execute-api.ap-northeast-1.amazonaws.com",
                    "apiId": "qnieunod45"
                },
                "body": null,
                "isBase64Encoded": false
            }            
            """
            cmd = commands.GetOrder(order_id=path_parameters.get('order_id'))

        # elif re.fullmatch('/orders/[0-9a-f]+/cancel', path) and http_method == 'POST':
        #     cmd = commands.CancelOrder(order_id=path_parameters.get('order_id'))
        #
        # elif re.fullmatch('/orders/[0-9a-f]+/revise', path) and http_method == 'POST':
        #     d = json.loads(body_json, parse_float=decimal.Decimal)
        #     delivery_information = order_history_model.DeliveryInformation.from_dict(
        #                                                         d['delivery_information'])
        #     revised_order_line_items = [order_history_model.RevisedOrderLineItem.from_dict(item)
        #                                 for item in d['revised_order_line_items']]
        #     order_revision = order_history_model.OrderRevision(
        #                                     delivery_information=delivery_information,
        #                                     revised_order_line_items=revised_order_line_items)
        #     cmd = commands.ReviseOrder(order_id=path_parameters.get('order_id'),
        #                                order_revision=order_revision)

        else:
            raise exceptions.UnsupportedRoute(f'Unsupported Route :{http_method}')

        resp = HANDLER.commands_handler(cmd)

        resp_ = None
        if isinstance(resp, list):
            resp_ = [order.to_dict() for order in resp]

        elif isinstance(resp, order_history_model.Order):
            resp_ = resp.to_dict()
        else:
            raise exceptions.UnsupportedType(f'resp: {resp}')

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
        print(str(e))
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to perform operation.',
                'errorMsg': str(e),
            })
        }
