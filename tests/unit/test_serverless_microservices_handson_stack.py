import aws_cdk as core
import aws_cdk.assertions as assertions

from stacks.serverless_microservices_handson_stack import ServerlessMicroservicesHandsonStack

# example tests. To run these tests, uncomment this file along with the example
# resource in serverless_microservices_handson/serverless_microservices_handson_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ServerlessMicroservicesHandsonStack(app, "serverless-microservices-handson")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
