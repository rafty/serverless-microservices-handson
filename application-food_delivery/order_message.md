
# Restaurant Created Event from EventBridge

### Order Service lambda_handler.event
```json
{
    "version": "0",
    "id": "a036599d-fd7c-301f-9c6e-34dfc947e39e",
    "detail-type": "RestaurantCreated",
    "source": "com.restaurant.created",
    "account": "338456725408",
    "time": "2022-12-01T04:05:59Z",
    "region": "ap-northeast-1",
    "resources": [],
    "detail": {
        "event_id": "32ef7c373d3f461c88082729f89d1190",
        "restaurant_id": 11,
        "restaurant_address": {
            "zip": "94611",
            "city": "Oakland",
            "street1": "1 Main Street",
            "street2": "Unit 99",
            "state": "CA"
        },
        "SK": "CHANNEL#RestaurantCreated#EVENTID#32ef7c373d3f461c88082729f89d1190",
        "menu_items": [
            {
                "price": {
                    "currency": "JPY",
                    "value": 800
                },
                "menu_name": "Curry Rice",
                "menu_id": "000001"
            },
            {
                "price": {
                    "currency": "JPY",
                    "value": 1000
                },
                "menu_name": "Hamburger",
                "menu_id": "000002"
            },
            {
                "price": {
                    "currency": "JPY",
                    "value": 700
                },
                "menu_name": "Ramen",
                "menu_id": "000003"
            }
        ],
        "PK": "RESTAURANT#11",
        "restaurant_name": "skylark",
        "channel": "RestaurantCreated"
    }
}
```
### Order Service lambda_handler.context
```python
context = LambdaContext(
    [
        aws_request_id=1a0cab84-4573-4a74-8b50-bc885e3b9f84,
        log_group_name=/aws/lambda/order_service_function,
        log_stream_name=2022/12/01/[$LATEST]c813b9d8ce5f481188e1ebfcbfdc547e,
        function_name=order_service_function,
        memory_limit_in_mb=128,
        function_version=$LATEST,
        invoked_function_arn=arn:aws:lambda:ap-northeast-1:338456725408:function:order_service_function,
        client_context=None,
        identity=CognitoIdentity([cognito_identity_id=None, cognito_identity_pool_id=None])
    ]
)
```
