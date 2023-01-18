import json
from consumer_layers.presentation import controller
from aws_xray_sdk import core as x_ray

x_ray.patch_all()


def lambda_handler(event, context):

    print(json.dumps(event))
    print(context)

    response = None
    if event.get('Records', None):  # from SQS
        pass
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

    else:  # from AapGateway
        response = controller.rest_invocation(event)

    return response
