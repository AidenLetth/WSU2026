from aws_cdk import (
    Stack,
    pipelines as pipeline_,
    aws_codepipeline as aws_codepipeline,
    SecretValue
)
from constructs import Construct


class AidenPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source = pipeline_.CodePipelineSource.git_hub(
            repo_string="AidenLetth/WSU2026", 
            branch="main",
            authentication=SecretValue.secrets_manager("githubSecret"),
            trigger=aws_codepipeline.CodePipelineTrigger.GITHUB("POLL")
        )

        synth = pipeline_.ShellStep(
            id="Synth",
            input=source,
            commands=[
                "npm install -g aws-cdk",
                "cd aiden/",
                "pip install -r requirements.txt",
                "cdk synth"
            ],
            primary_output_directory="aiden/cdk.out"
        )

        pipeline = pipeline_.CodePipeline(
            self,
            id="AidenPipeline",
            synth=synth,
        )
