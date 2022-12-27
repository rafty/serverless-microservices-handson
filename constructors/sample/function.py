from constructs import Construct
from aws_cdk import aws_lambda


class SampleFunctionConstructor(Construct):

    def __init__(self, scope: "Construct", id_: str, props: dict) -> None:
        super().__init__(scope, id_)
        self.props = props
        self.function = self.create_basket_function()

    def create_basket_function(self) -> aws_lambda.Function:

        function = aws_lambda.Function(
            self,
            'SampleFunction',
            function_name='sample_function',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset('application-food_delivery/sample_service/sample_function'),
            environment={
                'PRIMARY_KEY': 'userName',
            }
        )
        return function

    # @property
    # def function(self) -> aws_lambda.IFunction:
    #     return self._function
