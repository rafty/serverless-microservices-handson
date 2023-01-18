import json
from order_layers.presentation import controller
from aws_xray_sdk import core as x_ray

x_ray.patch_all()


def lambda_handler(event, context):

    print(json.dumps(event))
    print(context)

    response = None
    if event.get('Records', None):  # from SQS
        # SQS Invocation
        # sqs_invocation(event)
        # 今回はない
        pass
    elif event.get('detail-type', None):  # from EventBridge
        # Event Bridge Invocation
        controller.eventbus_invocation(event)

    elif event.get('task_context', {}).get('value', None):  # from StepFunctions
        """
        {
            "task_context": {
                "type": 1,
                "value": {
                    "state_machine": "OrderCreateSaga",
                    "action": "APPROVE_ORDER"
                }
            },
            "input": {...}
        }
        """
        response = controller.stepfunctions_invocation(event)

    else:  # from api gateway
        response = controller.rest_invocation(event)

    return response
