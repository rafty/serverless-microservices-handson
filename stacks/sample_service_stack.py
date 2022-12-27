from aws_cdk import Stack
from constructs import Construct
from constructors.sample import function


class SampleServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        order_table = function.SampleFunctionConstructor(self,
                                                         'SampleFunctionConstructor',
                                                         props={})
