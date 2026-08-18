from resources import constants           
from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as lambda_,
    RemovalPolicy,
    aws_events as events_,
    aws_events_targets as targets_,
    Duration,
    aws_iam as iam_,
    aws_cloudwatch as cw,
)
from constructs import Construct

class AidenStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/Role.html#aws_cdk.aws_iam.Role
        #Create a role for the Lambda function with CloudWatchFullAccess policy
        user_role = iam_.Role(self,"CWrole",
            assumed_by=iam_.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[iam_.ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess")]
        )
        user_role.apply_removal_policy(RemovalPolicy.DESTROY)

        #http://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_lambda/README.html
        #Created lambda function 
        fn = lambda_.Function(
            self,
            "webhealthapplication",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="webhealth.lambda_handler",
            code=lambda_.Code.from_asset("./resources"),
            role=user_role,
            timeout=Duration.seconds(30) #if the function takes longer than 30 seconds, it will timeout
        )

        fn.apply_removal_policy(RemovalPolicy.DESTROY)
    
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events/Schedule.html#aws_cdk.aws_events.Schedule
        #Create a rule to trigger the Lambda function on a schedule
        rule = events_.Rule(self, "Rule",
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events/Schedule.html#aws_cdk.aws_events.Schedule
        #Create a schedule to trigger the Lambda function
            schedule=events_.Schedule.rate(Duration.minutes(5)),
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events_targets/LambdaFunction.html#aws_cdk.aws_events_targets.LambdaFunction
        #Create a target for the Lambda function
            targets=[targets_.LambdaFunction(fn)]
        )
        rule.apply_removal_policy(RemovalPolicy.DESTROY)

        
        #Push Cloudwatch dashboard (just name without any widgets)
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Dashboard.html#aws_cdk.aws_cloudwatch.Dashboard
        dashboard = cw.Dashboard(
            self,
            "WebHealthDashboard",
            dashboard_name="WebHealthDashboard"
        )
        #Define metrics 
        latencyMetric = {}
        availabilityMetric = {}
        responseSizeMetric = {}

        #http ://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Metric.html#aws_cdk.aws_cloudwatch.Metric
        #Cloudwatch latency, availability and response size metric
        for website in constants.WEBSITES:
            latencyMetric[website] = cw.Metric(
                namespace=constants.namespace,
                metric_name=constants.metricLatency,
                dimensions_map={
                    "Website": website
                },

                 )
            availabilityMetric[website] = cw.Metric(
            namespace=constants.namespace,
            metric_name=constants.metricAvailability,
            dimensions_map={
                "Website": website
            },
            )
            responseSizeMetric[website] = cw.Metric(
            namespace=constants.namespace,
            metric_name=constants.metricResponseSize,
            dimensions_map={
                "Website": website
            },
           )

        #Add widgets to the dashboard (total 9, 3 for each website), but can be combined into 3 widgets for each website with 3 metrics in each widget
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/GraphWidget.html#aws_cdk.aws_cloudwatch.GraphWidget
        for website in constants.WEBSITES:
                dashboard.add_widgets(
                cw.GraphWidget(
                    title= website,
                    left=[availabilityMetric[website],
                          latencyMetric[website],],
                    right=[responseSizeMetric[website]],
                    width=12,
                    height=6
                )
                )

        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html#aws_cdk.aws_cloudwatch.Alarm
        #Set an alarm for availability,latency and status code metrics
                cw.Alarm(
                self,
                f"AvailabilityAlarm-{website}",
                metric=availabilityMetric[website],
                threshold=1,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
                )
                cw.Alarm(
                self,
                f"LatencyAlarm-{website}",
                metric=latencyMetric[website],
                threshold=0.23,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                 )
                cw.Alarm(
                self,
                f"ResponseSizeAlarm-{website}",
                metric=responseSizeMetric[website],
                threshold=150,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
                )

       
            