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
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_cloudwatch_actions as cw_actions,
    aws_dynamodb as dynamodb,       
    aws_codedeploy as codedeploy
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
            timeout=Duration.seconds(30) #if the function takes longer than 30 seconds, it will timeout, when do test in AWS Lambda, it will fail if do not set this timeout to 30 seconds
        )

        fn.apply_removal_policy(RemovalPolicy.DESTROY)
    
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Version.html#aws_cdk.aws_lambda.Version
        #create a version of the current lambda
        current_version = fn.current_version
        #Create an alias that points to the current version of the Lambda function
        live_alias = lambda_.Alias(
            self,
            "LiveAlias",
            alias_name="live",
            version=current_version
        )
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events/Schedule.html#aws_cdk.aws_events.Schedule
        #Create a rule to trigger the Lambda function on a schedule
        rule = events_.Rule(self, "Rule",
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events/Schedule.html#aws_cdk.aws_events.Schedule
        #Create a schedule to trigger the Lambda function
            schedule=events_.Schedule.rate(Duration.minutes(5)),
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events_targets/LambdaFunction.html#aws_cdk.aws_events_targets.LambdaFunction
        #Create a target for the Lambda function
            targets=[targets_.LambdaFunction(live_alias)]
        )
        rule.apply_removal_policy(RemovalPolicy.DESTROY)


        #Create an SNS topic (w6,7) to send notifications when an alarm is triggered
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html#aws_cdk.aws_sns.Topic
        alarm_topic = sns.Topic(
            self,
            "WHAlarmTopic",
            display_name="WHAlarm Notifications",
        )

        #An email subscription to SNS to receive notifications 
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/EmailSubscription.html#aws_cdk.aws_sns_subscriptions.EmailSubscription
        alarm_topic.add_subscription(subscriptions.EmailSubscription("janpan269@gmail.com"))

        #Push Cloudwatch dashboard (just name without any widgets)
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Dashboard.html#aws_cdk.aws_cloudwatch.Dashboard
        dashboard = cw.Dashboard(
            self,
            "WebHealthDashboard",
        )
        #Monitor how often the crawler runs, how long and whether it fails

        #how many times is the lambda crawler invoked
        invocationMetric= fn.metric_invocations(
             period=Duration.minutes(10),
             statistic="Sum"
        )

        #how long does the lambda crawler take to run
        durationMetric= fn.metric_duration(
            period=Duration.minutes(5),
            statistic ="Maximum" #timeout is 30 seconds, so if the crawler takes longer than 20 seconds, it will timeout and fail
        )
        #how many times does the lambda crawler fail
        errorMetric= fn.metric_errors(
            period=Duration.minutes(5),
            statistic="Sum"
        )
         # add Lambda operational metrics to the dashboard
        dashboard.add_widgets(
            cw.GraphWidget(
                title="Web Crawler Operational Health",
                left=[
                    invocationMetric,
                    errorMetric
                ],
                right=[
                    durationMetric
                ],
                width=12,
                height=6
            )
        )

        
        # Alarm if the scheduled crawler does not run
        lambda_invocation_alarm = cw.Alarm(
            self,
            "LambdaInvocationAlarm",
            metric=invocationMetric,
            threshold=1,
            evaluation_periods=1,
            comparison_operator=
                cw.ComparisonOperator.LESS_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.BREACHING
        )
        # Alarm if one crawler run takes more than 20 seconds
        lambda_duration_alarm = cw.Alarm(
            self,
            "LambdaDurationAlarm",
            metric=durationMetric,
            threshold=20000, # 20 seconds in milliseconds
            evaluation_periods=1,
            comparison_operator=
                cw.ComparisonOperator.GREATER_THAN_THRESHOLD
        )

        # Alarm if Lambda reports an execution error
        lambda_error_alarm = cw.Alarm(
            self,
            "LambdaErrorAlarm",
            metric=errorMetric,
            threshold=1, # 1 error
            evaluation_periods=1,
            comparison_operator=
                cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )

        # Send operational alarms to the existing SNS topic
        operational_alarms = [
            lambda_error_alarm,
            lambda_duration_alarm,
            lambda_invocation_alarm
        ]

        for alarm in operational_alarms:
            alarm.add_alarm_action(
                cw_actions.SnsAction(alarm_topic)
            )
        #canary deployment with automatic rollback if the new version of the Lambda function fails
         #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_codedeploy/AutoRollbackConfig.html#aws_cdk.aws_codedeploy.AutoRollbackConfig
        deployment_group = codedeploy.LambdaDeploymentGroup(
            self,
            "WebCrawlerDeploymentGroup",
            alias=live_alias,
            deployment_config=codedeploy.LambdaDeploymentConfig.CANARY_10_PERCENT_5_MINUTES, # in the first 5 mins, deploy 10% of version 1, 90% of version 2, if OK, 100% of version 2 will be deployed, if not, rollback to version 1
           #error and duration alarms will be used to monitor the new version of the Lambda function, invocation is not used a low invocation count may be caused by scheduling or traffic rather than a faulty deployment  
            alarms=[
                lambda_error_alarm,
                lambda_duration_alarm,],
            #2 options for auto rollback: deployment_in_alarm and failed_deployment, rollback will be happened if any of the alarms are triggered or if the deployment fails
            auto_rollback=codedeploy.AutoRollbackConfig(
                deployment_in_alarm = True,
                failed_deployment = True
            )
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
        #Set an alarm for availability,latency and response size metrics
                availabilityAlarm = cw.Alarm(
                self,
                f"AvailabilityAlarm-{website}",
                metric=availabilityMetric[website],
                threshold=1,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
                )
                #Add an action to alarm to send a notifiaction
                #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch_actions/SnsAction.html#aws_cdk.aws_cloudwatch_actions.SnsAction
                availabilityAlarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

                latencyAlarm = cw.Alarm(
                self,
                f"LatencyAlarm-{website}",
                metric=latencyMetric[website],
                threshold=0.23,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                 )
                latencyAlarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))
                responseSizeAlarm = cw.Alarm(
                self,
                f"ResponseSizeAlarm-{website}",
                metric=responseSizeMetric[website],
                threshold=150,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
                )
                responseSizeAlarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        #Create a DynamoDB table to store alarm notifications 
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html#aws_cdk.aws_dynamodb.Table
        table = dynamodb.Table(
            self,
            "AlarmNotificationsTable",
            partition_key=dynamodb.Attribute(
                name="alarm_id",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

        #Create Lambda logger (function) (bridge between SNS and DynamoDB) to log alarm notifications to DynamoDB table
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html#aws_cdk.aws_lambda.Function
        alarm_logger = lambda_.Function(
            self,
            "AlarmLogger",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="alarm.lambda_handler",
            code=lambda_.Code.from_asset("./resources"),
            environment={
                "DYNAMODB_TABLE_NAME": table.table_name
            },
            timeout=Duration.seconds(30), #(optional) but if the function takes longer than 30 seconds, it will timeout (lambda in aws)
        )
        #Grant the Lambda function permission to write to the DynamoDB table
        #https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html#aws_cdk.aws_dynamodb.Table.grant_write_data
        table.grant_write_data(alarm_logger)  

        #Subscribe to receive notifications in the second way (Lambda function) when an alarm is triggered
        alarm_topic.add_subscription(subscriptions.LambdaSubscription(alarm_logger))
