# Aiden Web Health Monitoring
## Project Overview
Aiden Web Health Monitoring is an AWS CDK project that monitors the availability and performance of multiple websites.

The project uses AWS Lambda to crawl website targets, Amazon DynamoDB to store the target list, Amazon CloudWatch to monitor website and Lambda operational health, and Amazon API Gateway to provide a public REST CRUD interface for managing crawler targets.

The project also uses AWS CodePipeline to automate testing and deployment across multiple stages.


## Project Objectives

- Monitor multiple websites automatically.
- Measure website Availability, Latency, and Response Size.
- Publish custom metrics to Amazon CloudWatch.
- Monitor Lambda Invocations, Duration, and Errors.
- Trigger CloudWatch alarms when abnormal behaviour is detected.
- Send alarm notifications using Amazon SNS.
- Store alarm notification information in DynamoDB.
- Store crawler target websites in DynamoDB.
- Manage crawler targets through a public REST API.
- Implement Create, Read, Update, and Delete operations.
- Measure DynamoDB read and write time.
- Automate testing using unit, functional, and integration tests.
- Deploy through multiple CI/CD stages.
- Use Lambda versions, aliases, canary deployment, and automatic rollback.



## Project Structure

```text
Aiden/
├── aiden/
│   ├── __init__.py
│   ├── aiden_stack.py
│   ├── pipeline_stack.py
│   └── pipeline_stage.py
│
├── resources/
│   ├── alarm.py
│   ├── constants.py
│   ├── CWdata.py
│   ├── target_api.py
│   └── webhealth.py
│
├── tests/
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_aiden_stack.py
│   │   ├── test_target_api_unit.py
│   │   └── test_wh_unit.py
│   │
│   ├── functional/
│   │   ├── __init__.py
│   │   ├── test_target_api_functional.py
│   │   └── test_wh_functional.py
│   │
│   └── integration/
│       ├── __init__.py
│       ├── test_target_api_integration.py
│       └── test_wh_integration.py
│
├── app.py
├── README.md
├── requirements.txt
├── requirements-dev.txt
└── cdk.json
```

## Architecture

```text
                         User
                          |
                          v
                  Amazon API Gateway
                          |
                          v
                     CRUD Lambda
                          |
                          v
                DynamoDB Targets Table
                          |
                          v
                  Web Crawler Lambda
                          |
                          v
                    Target Websites
                          |
                          v
                  Amazon CloudWatch
                  /              \
          Dashboard              Alarms
                                   |
                                   v
                              Amazon SNS
                              /          \
                           Email      Alarm Logger
                                         |
                                         v
                                     DynamoDB


GitHub Repository
       |
       v
AWS CodePipeline
       |
       v
      Synth
       |
       v
Unit Test Blocker
       |
       v
Unit Test Stage
       |
       v
Functional Test Blocker
       |
       v
Functional Test Stage
       |
       v
Integration Test Blocker
       |
       v
Integration Test Stage
       |
       v
Manual Production Approval
       |
       v
Production Stage
       |
       v
Lambda Version
       |
       v
Live Alias
       |
       v
CodeDeploy Canary Deployment
       |
       +-------------------------------+
       |                               |
    Healthy                          Alarm
       |                               |
       v                               v
Complete Deployment           Automatic Rollback

```

## Main Components

### AWS CDK

AWS CDK is used to define and deploy the project infrastructure as code.

The main application stack is `AidenStack`, while `pipeline_stack.py` and `pipeline_stage.py` manage the CI/CD pipeline and deployment stages.

### AWS Lambda

The project uses three main Lambda functions:

- `webhealth.py` monitors website targets.
- `target_api.py` handles CRUD operations for crawler targets.
- `alarm.py` stores CloudWatch alarm information in DynamoDB.

### Amazon DynamoDB

DynamoDB is used for two purposes:

- Store crawler website targets.
- Store alarm notification records.

The crawler reads the target list from DynamoDB instead of using a permanently hard-coded website list.

### Amazon API Gateway

API Gateway provides a public REST API for managing crawler targets.

| Method | Endpoint | Operation |
| --- | --- | --- |
| POST | `/targets` | Create target |
| GET | `/targets` | Read all targets |
| GET | `/targets/{target_id}` | Read one target |
| PUT | `/targets/{target_id}` | Update target |
| DELETE | `/targets/{target_id}` | Delete target |

DynamoDB read and write time is also measured and returned in milliseconds.

### Amazon CloudWatch

CloudWatch is used for website monitoring and Lambda operational monitoring.

Website metrics:

- Availability
- Latency
- Response Size

Lambda metrics:

- Invocations
- Duration
- Errors

CloudWatch alarms are used to detect unhealthy behaviour.

### Amazon SNS

SNS sends notifications when CloudWatch alarms are triggered.

It can send email notifications and invoke the Alarm Logger Lambda.

---

## CI/CD Pipeline

AWS CodePipeline automates testing and deployment.

```text
GitHub
 |
 v
Synth
 |
 v
Unit Test Blocker
 |
 v
UnitTestStage
 |
 v
Functional Test Blocker
 |
 v
FunctionalTestStage
 |
 v
Integration Test Blocker
 |
 v
IntegrationTestStage
 |
 v
Manual Production Approval
 |
 v
ProdStage
```

Each test blocker must pass before the next stage can continue.

Production deployment requires manual approval.

---

## Canary Deployment and Rollback

The Web Crawler Lambda uses a published Lambda version and a `Live` alias.

AWS CodeDeploy uses a canary deployment strategy:

`CANARY_10_PERCENT_5_MINUTES`

This sends 10% of traffic to the new Lambda version for five minutes.

CloudWatch Error and Duration alarms monitor the deployment.

If the deployment fails or an alarm is triggered, CodeDeploy is configured to automatically rollback to the previous Lambda version.

---

## Automated Testing

The project uses PyTest for automated testing.

Current result:

```text
13 Unit Tests
9 Functional Tests
3 Integration Tests

25 Tests Passed
```

The Applied Project adds:

- 2 unit tests
- 1 functional test
- 1 integration test

Run all tests using:

```bash
python -m pytest
```

---

## Deployment

Validate the CDK application:

```bash
cdk synth
```

Deploy the pipeline:

```bash
cdk deploy AidenPipelineStack
```

After the pipeline is deployed, code changes pushed to GitHub automatically start the testing and deployment process.

---

## Current Status

The Web Health monitoring system, CloudWatch monitoring, SNS notifications, DynamoDB alarm logging, multi-stage CI/CD pipeline, Lambda canary deployment, automatic rollback, public CRUD API, and DynamoDB crawler target management have been implemented.

The complete automated test suite currently passes:

`25 passed`

---

## Author

**Aiden**
