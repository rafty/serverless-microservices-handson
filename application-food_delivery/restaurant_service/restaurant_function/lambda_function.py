import json
from restaurant_layers.presentation import controller


def lambda_handler(event, context):

    print(json.dumps(event))
    print(context)

    resp = None
    if event.get('Records', None):  # from SQS
        # SQS Invocation
        # sqs_invocation(event)
        # 今回はない
        pass
    elif event.get('detail-type', None):  # from event bridge
        # Event Bridge Invocation
        # 今回はEventBridgeからLambdaの呼び出しは無い
        pass
    else:  # from api gateway
        resp = controller.rest_invocation(event)

    return resp
