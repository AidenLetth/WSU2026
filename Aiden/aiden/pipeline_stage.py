from aws_cdk import (
    Stage
)
from constructs import Construct

from .aiden_stack import AidenStack


class AidenPipelineStage(Stage):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        AidenStack(
            self,
            "AidenStack"
        )