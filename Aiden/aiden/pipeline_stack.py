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
        
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/CodePipelineSource.html#aws_cdk.pipelines.CodePipelineSource.git_hub
        #first step is to define the source of the pipeline, which is a GitHub repository 
        #the authentication is done using a secret stored in AWS Secrets Manager
        source = pipeline_.CodePipelineSource.git_hub(
            repo_string="AidenLetth/WSU2026",
            branch="main",
            authentication=SecretValue.secrets_manager("githubSecret")
        )
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/ShellStep.html#aws_cdk.pipelines.ShellStep
        #the second step is to define the synth step, which is a ShellStep that runs the commands to synthesize the CDK app
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
        #Alpha Stage is a stage that runs the unit tests for the CDK app, it is added to the pipeline after the synth step
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/CodePipeline.html#aws_cdk.pipelines.CodePipeline.add_stage
        AlphaStage = AidenPipelineStage( self, "UnitTestStage")
        pipeline.add_stage (AlphaStage,
                            pre=[pipeline_.ShellStep("UnitTestBlocker",
                                 commands=[ "npm install -g aws-cdk",
                                   "cd Aiden/",
                                   "python -m pip install -r requirements.txt",
                                   "python -m pip install pytest",
                                   "python3 -m pytest"
                                   ] )
                                ]
                            )
        #Beta Stage is a stage that runs the integration tests for the CDK app, it is added to the pipeline after the Alpha Stage
        BetaStage = AidenPipelineStage( self, "IntegrationTestStage")
        pipeline.add_stage (BetaStage,
                            pre=[pipeline_.ShellStep("IntegrationTestBlocker",
                                 commands=[ "npm install -g aws-cdk",
                                   "cd Aiden/",
                                   "python -m pip install -r requirements.txt",
                                   "python -m pip install pytest",
                                   "python3 -m pytest"
                                   ] )
                                ]
                            )
