# Aiden Web Health Monitoring

Aiden Web Health Monitoring is an AWS CDK project that monitors the health and performance of multiple websites.

The application uses AWS Lambda to send real HTTP requests to each configured website, collect website health metrics, publish the metrics to Amazon CloudWatch, display them on a CloudWatch Dashboard, and evaluate CloudWatch Alarms.

## Project Objectives

- Monitor multiple websites automatically.
- Collect real Availability values.
- Measure real Latency values.
- Measure real Response Size values.
- Publish custom metrics to Amazon CloudWatch.
- Display website health data on a CloudWatch Dashboard.
- Configure CloudWatch Alarms for abnormal metric values.
- Use Amazon SNS for alarm notifications.
- Log alarm notifications in Amazon DynamoDB.
- Maintain project documentation and the GitHub Project board.


## Monitored Websites

1. https://www.ralphlauren.com
2. https://www.google.com
3. https://www.westernsydney.edu.au

The website list is defined in resources/constants.py.

## Metrics

| Metric | Description | Unit / Value
| ----------- | ----------- | -----------
| Availability | Shows whether a website request succeeds | 1 = available, 0 = unavailable
| Latency | Measures how long the website request takes | Seconds
| Status Code | Measures the amount of response data returned by the website | Bytes

The project monitors:

**3 websites × 3 metrics = 9 metric dimensions**

## Project Structure

```text
Aiden/
├── aiden/
│   ├── __init__.py
│   └── aiden_stack.py
├── resources/
│   ├── alarm.py
│   ├── constants.py
│   ├── CWdata.py
│   └── webhealth.py
├── app.py
├── README.md
├── requirements.txt
└── cdk.json
```

## Architecture

```text
Amazon EventBridge
        |
        | Scheduled trigger
        v
AWS Lambda - Web Health
        |
        | HTTP requests
        v
Monitored Websites
        |
        | Availability / Latency / Response Size
        v
Amazon CloudWatch
     /           \
Dashboard       Alarms
                   |
                   v
              Amazon SNS
              /        \
         Email       Alarm Logger
                         |
                         v
                    DynamoDB
```

## Main Components

### AWS CDK

AWS CDK is used to define and deploy the AWS infrastructure as code.

The main stack is:

`AidenStack`

The stack creates and configures the main AWS resources used by the project.

### AWS Lambda

The Web Health Lambda function is defined in:

`resources/webhealth.py`

It loops through the configured websites and performs a real HTTP request for each website.

For each request, the function collects:

- Availability
- Latency
- Response Size

### Amazon EventBridge

EventBridge automatically triggers the Web Health Lambda on a schedule.

The current monitoring schedule is:

`Every 5 minutes`

### Amazon CloudWatch

CloudWatch is used to:

- Store custom Web Health metrics.
- Display metrics on `WebHealthDashboard`.
- Evaluate metric thresholds using CloudWatch Alarms.
- Store Lambda execution logs.

### Amazon SNS

Amazon SNS is used to publish notifications when CloudWatch Alarm thresholds are breached.

SNS can notify subscribers such as an email subscription and can also trigger the alarm logging workflow.

### Amazon DynamoDB

DynamoDB is used to store alarm notification information so that alarm events can be reviewed later.

---

## Real Website Health Collection

The Web Health Lambda sends an HTTP request to each configured website.
This produces real metric values for each monitoring run.

---

## CloudWatch Metric Publishing

Metric publishing is handled by:

`resources/CWdata.py`

Each website is sent to CloudWatch as an individual `Website` dimension.
The custom CloudWatch namespace is:

`Aiden`

---

## CloudWatch Dashboard

The project creates a CloudWatch Dashboard named:

`WebHealthDashboard`

The dashboard contains one graph for each monitored website.

Each graph displays:

- Availability
- Latency
- Response Size

This allows the health of all monitored websites to be reviewed from a single dashboard.

---

## CloudWatch Alarms

CloudWatch Alarms evaluate the website metrics against configured thresholds.

The project includes alarms for:

- Availability
- Latency
- Response Size

Alarm thresholds should be reviewed after observing real website values because real latency and response size can vary between websites.

---

## SNS Alarm Notifications

When a CloudWatch Alarm enters the `ALARM` state, Amazon SNS is used to publish an alarm notification.

The notification workflow is:

```text
CloudWatch Alarm
        |
        v
Amazon SNS
     /      \
 Email    Alarm Logger
```

Email subscriptions must be confirmed before notification emails can be received.

---

## DynamoDB Alarm Logging

Alarm notifications can be logged in DynamoDB through the alarm logging Lambda.

The alarm log can contain information such as:

- Alarm name
- Alarm state
- Alarm reason
- Timestamp
- Alarm identifier

This provides a historical record of alarm events.

---

## Deployment

Activate the Python virtual environment:

```bash
source .venv/bin/activate
```

Install dependencies if required:

```bash
pip install -r requirements.txt
```

Check the CDK template:

```bash
cdk synth
```

Deploy the stack:

```bash
cdk deploy
```

---

## Testing

### Test the Web Health Lambda

1. Open AWS Lambda.
2. Select the Web Health Lambda function.
3. Create or select a test event.
4. Run the test.
5. Check the execution result and CloudWatch Logs.

A successful run should process all three websites.

Example output:

```text
Website: https://www.ralphlauren.com | Availability: 1 | Latency: ... | Response Size: ... bytes
Website: https://www.google.com | Availability: 1 | Latency: ... | Response Size: ... bytes
Website: https://www.westernsydney.edu.au | Availability: 1 | Latency: ... | Response Size: ... bytes
```

### Verify CloudWatch Metrics

Open:

`CloudWatch -> Metrics -> Aiden`

Check that each website has values for:

- Availability
- Latency
- Response Size

### Verify the Dashboard

Open:

`CloudWatch -> Dashboards -> WebHealthDashboard`

Confirm that all three website graphs update with current values.

### Verify Alarms

Open:

`CloudWatch -> Alarms`

Confirm that the alarm states match the current metric values and thresholds.

### Verify SNS

Trigger a threshold breach and confirm that the SNS notification is delivered to the configured subscriber.

### Verify DynamoDB

After an alarm notification is generated, open the DynamoDB alarm log table and confirm that the alarm record has been stored.

---

## GitHub Project Board

The project board is organised into five workflow columns:

1. User Stories / Backlog
2. Features
3. In Progress
4. In Review
5. Done

The board is updated to reflect the current implementation, testing, and verification status of the Web Health project.

---

## Author

**Aiden**

