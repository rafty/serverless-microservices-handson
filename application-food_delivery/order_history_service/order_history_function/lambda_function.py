import json
from order_history_layers.presentation import controller
from aws_xray_sdk import core as x_ray

x_ray.patch_all()


def lambda_handler(event, context):

    print(json.dumps(event))
    print(context)

    response = None
    if event.get('detail-type', None):  # from EventBridge
        # Event Bridge Invocation
        controller.eventbus_invocation(event)

    else:  # from api gateway
        response = controller.rest_invocation(event)

    return response
