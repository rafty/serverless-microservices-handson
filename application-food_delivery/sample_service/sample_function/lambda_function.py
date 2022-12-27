import json
# from domain import model
from sample_layers.domain import model


def lambda_handler(event, context):
    print(json.dumps(event))
    print(context)

    address = None
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
        order = model.Order()
        print(order)
        print(order.name)
        # address = order.address
    return True
