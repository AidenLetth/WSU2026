from aws_cdk import (
    Stack,
    pipelines as pipeline_,
    SecretValue
)
from constructs import Construct
from .pipeline_stage import AidenPipelineStage


class AidenPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source = pipeline_.CodePipelineSource.git_hub(
            repo_string="AidenLetth/WSU2026",
            branch="main",
            authentication=SecretValue.secrets_manager("githubSecret")
        )

        synth = pipeline_.ShellStep(
            "Synth",
            input=source,
            commands=[
                "npm install -g aws-cdk",
                "cd Aiden/",
                "python -m pip install -r requirements.txt",
                "cdk synth"
            ],
            primary_output_directory="Aiden/cdk.out"
        )

        pipeline = pipeline_.CodePipeline(
            self,
            "AidenPipeline",
            synth=synth
        )
        #Alpha 
        AlphaStage = AidenPipelineStage( self, "UnitTestStage")
        pipeline.add_stage (AlphaStage,
                            pre=[pipeline_.ShellStep("UnitTestBlocker",
                                 commands=[ "npm install -g aws-cdk",
                                   "cd Aiden/",
                                   "python -m pip install -r requirements.txt",
                                   "python -m pip install pytest",
                                   "python3 -m pytest"
                                   ]
        )
                                ]
                            )
       