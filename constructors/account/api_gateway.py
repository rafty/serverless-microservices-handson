from constructs import Construct
from aws_cdk import aws_apigateway


class AccountRestApiConstructor(Construct):

    def __init__(self, scope: "Construct", id: str, props: dict) -> None:
        super().__init__(scope, id)

        self.api: aws_apigateway.LambdaRestApi = None
        self.props = props

        self.account_api()

    def account_api(self) -> None:
        self.api = aws_apigateway.LambdaRestApi(
            self,
            'AccountServiceRestApi',
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

            /accounts
                - POST          : create account

            /accounts?consumer_id=1
                - GET           : fetch multi accounts

        """
        accounts = self.api.root.add_resource('accounts')
        accounts.add_method('POST')
        accounts.add_method('GET')

        # multi_account = accounts.add_resource('{consumer_id}')
        # multi_account.add_method('GET')
