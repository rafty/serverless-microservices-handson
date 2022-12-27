import json
from kitchen_layer.presentation import controller


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
                    "action": "CREATE_TICKET"
                }
            },
            "input": {...}
        }
        """
        response = controller.stepfunctions_invocation(event)

    elif event.get('resource', None) and event.get('path', None):  # from api gateway
        response = controller.rest_invocation(event)

    else:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Unsupported Request.',
                'errorMsg': f'Unsupported Request.',
            })
        }

    return response
