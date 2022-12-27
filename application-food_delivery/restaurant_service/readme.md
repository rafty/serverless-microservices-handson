# REST 
```
CreateRestaurantRequest
PATH = /restaurants
POST
    restaurant_name
    restaurant_address
    menu_items
---
Response
    restaurant_id
```

# CreateRestaurantRequest lambda_handler.event
```json
{
    "resource": "/restaurants",
    "path": "/restaurants",
    "httpMethod": "POST",
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
        "Content-Type": "text/plain",
        "Host": "7pzp2u9fnl.execute-api.ap-northeast-1.amazonaws.com",
        "Postman-Token": "6add5762-369e-40f4-9c6a-b378be44adcb",
        "User-Agent": "PostmanRuntime/7.29.2",
        "Via": "1.1 c242a437dc6226d46fcad5a8f03d8d80.cloudfront.net (CloudFront)",
        "X-Amz-Cf-Id": "o8iDjOxxyz9vMqxwcN1eEVT6rcCb_kxQYDo81o_hOhgPqkrdJY68Bg==",
        "X-Amzn-Trace-Id": "Root=1-63871211-7e65f25620f2094953cdc49a",
        "X-Forwarded-For": "60.116.89.182, 130.176.189.109",
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
        "Content-Type": [
            "text/plain"
        ],
        "Host": [
            "7pzp2u9fnl.execute-api.ap-northeast-1.amazonaws.com"
        ],
        "Postman-Token": [
            "6add5762-369e-40f4-9c6a-b378be44adcb"
        ],
        "User-Agent": [
            "PostmanRuntime/7.29.2"
        ],
        "Via": [
            "1.1 c242a437dc6226d46fcad5a8f03d8d80.cloudfront.net (CloudFront)"
        ],
        "X-Amz-Cf-Id": [
            "o8iDjOxxyz9vMqxwcN1eEVT6rcCb_kxQYDo81o_hOhgPqkrdJY68Bg=="
        ],
        "X-Amzn-Trace-Id": [
            "Root=1-63871211-7e65f25620f2094953cdc49a"
        ],
        "X-Forwarded-For": [
            "60.116.89.182, 130.176.189.109"
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
    "pathParameters": null,
    "stageVariables": null,
    "requestContext": {
        "resourceId": "uj8w4w",
        "resourcePath": "/restaurants",
        "httpMethod": "POST",
        "extendedRequestId": "cZ_C1El1NjMFmHg=",
        "requestTime": "30/Nov/2022:08:19:29 +0000",
        "path": "/prod/restaurants",
        "accountId": "338456725408",
        "protocol": "HTTP/1.1",
        "stage": "prod",
        "domainPrefix": "7pzp2u9fnl",
        "requestTimeEpoch": 1669796369988,
        "requestId": "3fdcebe3-856f-4a3c-963f-d248d55d89ca",
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
        "domainName": "7pzp2u9fnl.execute-api.ap-northeast-1.amazonaws.com",
        "apiId": "7pzp2u9fnl"
    },
    "body": "{\n    \"restaurant_name\": \"skylark\",\n    \"restaurant_address\": {\n        \"street1\": \"1 Main Street\",\n        \"street2\": \"Unit 99\",\n        \"city\": \"Oakland\",\n        \"state\": \"CA\",\n        \"zip\": \"94611\"\n    },\n    \"menu_items\": [\n        {\n            \"menu_id\": \"000001\",\n            \"menu_name\": \"Curry Rice\",\n            \"price\": {\n                        \"value\": 800,\n                        \"currency\": \"JPY\"\n                     }\n        },\n        {\n            \"menu_id\": \"000002\",\n            \"menu_name\": \"Hamburger\",\n            \"price\": {\n                        \"value\": 1000,\n                        \"currency\": \"JPY\"\n                     }\n        },\n        {\n            \"menu_id\": \"000003\",\n            \"menu_name\": \"Ramen\",\n            \"price\": {\n                        \"value\": 700,\n                        \"currency\": \"JPY\"\n                     }\n        }\n    ]\n}",
    "isBase64Encoded": false
}
```


```
GetRestaurantRequest
PATH = /restaurants/{restaurant_id}
GET
---
Response
    restaurant_id
    restaurant_name
    restaurant_address
    menu_items
```

# GetRestaurantRequest lambda_handler.event
```json
{
    "resource": "/restaurants/{restaurant_id}",
    "path": "/restaurants/9",
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
        "Host": "7pzp2u9fnl.execute-api.ap-northeast-1.amazonaws.com",
        "Postman-Token": "1a377536-6253-4830-bf57-76467f1120d4",
        "User-Agent": "PostmanRuntime/7.29.2",
        "Via": "1.1 c242a437dc6226d46fcad5a8f03d8d80.cloudfront.net (CloudFront)",
        "X-Amz-Cf-Id": "6Um8pssfFDIjspBWhjYpFvzPHZSyb0RrbbzZwiPd_ik3KE_l-m2C9g==",
        "X-Amzn-Trace-Id": "Root=1-63871239-10e538ef62757b53200dc642",
        "X-Forwarded-For": "60.116.89.182, 130.176.189.101",
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
            "7pzp2u9fnl.execute-api.ap-northeast-1.amazonaws.com"
        ],
        "Postman-Token": [
            "1a377536-6253-4830-bf57-76467f1120d4"
        ],
        "User-Agent": [
            "PostmanRuntime/7.29.2"
        ],
        "Via": [
            "1.1 c242a437dc6226d46fcad5a8f03d8d80.cloudfront.net (CloudFront)"
        ],
        "X-Amz-Cf-Id": [
            "6Um8pssfFDIjspBWhjYpFvzPHZSyb0RrbbzZwiPd_ik3KE_l-m2C9g=="
        ],
        "X-Amzn-Trace-Id": [
            "Root=1-63871239-10e538ef62757b53200dc642"
        ],
        "X-Forwarded-For": [
            "60.116.89.182, 130.176.189.101"
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
        "restaurant_id": "9"
    },
    "stageVariables": null,
    "requestContext": {
        "resourceId": "eg98ui",
        "resourcePath": "/restaurants/{restaurant_id}",
        "httpMethod": "GET",
        "extendedRequestId": "cZ_JDFIHtjMF0EA=",
        "requestTime": "30/Nov/2022:08:20:09 +0000",
        "path": "/prod/restaurants/9",
        "accountId": "338456725408",
        "protocol": "HTTP/1.1",
        "stage": "prod",
        "domainPrefix": "7pzp2u9fnl",
        "requestTimeEpoch": 1669796409794,
        "requestId": "fcae4caf-4908-4e7c-9b79-7ca1f1b64c48",
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
        "domainName": "7pzp2u9fnl.execute-api.ap-northeast-1.amazonaws.com",
        "apiId": "7pzp2u9fnl"
    },
    "body": null,
    "isBase64Encoded": false
}
```

# Restaurant Event Lambda from DynamoDB Stream
## restaurant_event_function.event
```json
{
    "Records": [
        {
            "eventID": "32b554bad3737253edf777843939305a",
            "eventName": "INSERT",
            "eventVersion": "1.1",
            "eventSource": "aws:dynamodb",
            "awsRegion": "ap-northeast-1",
            "dynamodb": {
                "ApproximateCreationDateTime": 1669805739,
                "Keys": {
                    "SK": {
                        "S": "CHANNEL#RestaurantCreated#EVENTID#d950c73b4ea540c1a6f31e1c1622e5a4"
                    },
                    "PK": {
                        "S": "RESTAURANT#10"
                    }
                },
                "NewImage": {
                    "event_id": {
                        "S": "d950c73b4ea540c1a6f31e1c1622e5a4"
                    },
                    "restaurant_id": {
                        "N": "10"
                    },
                    "restaurant_address": {
                        "M": {
                            "zip": {
                                "S": "94611"
                            },
                            "city": {
                                "S": "Oakland"
                            },
                            "street1": {
                                "S": "1 Main Street"
                            },
                            "street2": {
                                "S": "Unit 99"
                            },
                            "state": {
                                "S": "CA"
                            }
                        }
                    },
                    "SK": {
                        "S": "CHANNEL#RestaurantCreated#EVENTID#d950c73b4ea540c1a6f31e1c1622e5a4"
                    },
                    "menu_items": {
                        "L": [
                            {
                                "M": {
                                    "price": {
                                        "M": {
                                            "currency": {
                                                "S": "JPY"
                                            },
                                            "value": {
                                                "N": "800"
                                            }
                                        }
                                    },
                                    "menu_name": {
                                        "S": "Curry Rice"
                                    },
                                    "menu_id": {
                                        "S": "000001"
                                    }
                                }
                            },
                            {
                                "M": {
                                    "price": {
                                        "M": {
                                            "currency": {
                                                "S": "JPY"
                                            },
                                            "value": {
                                                "N": "1000"
                                            }
                                        }
                                    },
                                    "menu_name": {
                                        "S": "Hamburger"
                                    },
                                    "menu_id": {
                                        "S": "000002"
                                    }
                                }
                            },
                            {
                                "M": {
                                    "price": {
                                        "M": {
                                            "currency": {
                                                "S": "JPY"
                                            },
                                            "value": {
                                                "N": "700"
                                            }
                                        }
                                    },
                                    "menu_name": {
                                        "S": "Ramen"
                                    },
                                    "menu_id": {
                                        "S": "000003"
                                    }
                                }
                            }
                        ]
                    },
                    "PK": {
                        "S": "RESTAURANT#10"
                    },
                    "restaurant_name": {
                        "S": "skylark"
                    }
                },
                "SequenceNumber": "3672700000000019868689746",
                "SizeBytes": 537,
                "StreamViewType": "NEW_IMAGE"
            },
            "eventSourceARN": "arn:aws:dynamodb:ap-northeast-1:338456725408:table/RestaurantEvent/stream/2022-11-30T10:29:55.261"
        }
    ]
}
```

``````