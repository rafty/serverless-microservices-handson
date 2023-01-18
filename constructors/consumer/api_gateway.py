from constructs import Construct
from aws_cdk import aws_apigateway


class ConsumerRestApiConstructor(Construct):

    def __init__(self, scope: "Construct", id: str, props: dict) -> None:
        super().__init__(scope, id)

        self.api: aws_apigateway.LambdaRestApi = None
        self.props = props

        self.consumer_api()

    def consumer_api(self) -> None:
        self.api = aws_apigateway.LambdaRestApi(
            self,
            'ConsumerServiceRestApi',
            handler=self.props['function'],
            proxy=False,
            deploy_options=aws_apigateway.StageOptions(
                data_trace_enabled=True,
                logging_level=aws_apigateway.MethodLoggingLevel.INFO,
                metrics_enabled=True,
                tracing_enabled=True,
            )
        )
        self.rest_resource_and_method()

    def rest_resource_and_method(self) -> None:
        """
        Resource and Method

            /consumers
                - POST          : create consumer

            /consumers/{consumer_id}
                - GET           : fetch single consumer

        """
        consumers = self.api.root.add_resource('consumers')
        consumers.add_method('POST')

        single_consumer = consumers.add_resource('{consumer_id}')
        single_consumer.add_method('GET')
