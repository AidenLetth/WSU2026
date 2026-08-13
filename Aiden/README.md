# Aiden Web Health Monitoring

This project uses AWS CDK, AWS Lambda, EventBridge, and CloudWatch to monitor the health and performance of multiple websites.

## Project Objectives

- Monitor multiple websites.
- Measure availability, latency, and HTTP status code.
- Publish metrics to CloudWatch.
- Create a CloudWatch Dashboard.
- Configure CloudWatch Alarms.
- Automate monitoring using EventBridge.
- Manage documentation using Markdown and GitHub.

## Technologies

| Technology | Purpose |
| ----------- | ----------- |
| Python | Application development |
| AWS CDK | Infrastructure as Code |
| AWS Lambda | Web health monitoring |
| EventBridge | Schedule Lambda execution |
| CloudWatch | Metrics, Dashboard and Alarms |
| GitHub | Version control and project management |

## Monitored Websites

1. https://www.ralphlauren.com
2. https://www.google.com
3. https://www.westernsydney.edu.au

## Metrics

| Metric | Description |
| ----------- | ----------- |
| Availability | Indicates whether the website is available |
| Latency | Measures website response time |
| Status Code | Records the HTTP response code |

The project monitors:

**3 websites × 3 metrics = 9 metric dimensions**

## Project Structure

```text
Aiden/
├── aiden/
│   ├── __init__.py
│   └── aiden_stack.py
├── resources/
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
EventBridge
     |
     v
AWS Lambda
     |
     v
CloudWatch
  /       \
Dashboard  Alarms
```

## Lambda Function

The Lambda function is implemented in `webhealth.py`.

## EventBridge

The Lambda function is automatically triggered every 1 minute.

```python
schedule=events_.Schedule.rate(Duration.minutes(1))
```

## CloudWatch Dashboard

A CloudWatch Dashboard named `WebHealthDashboard` was created.

The dashboard displays:

- Availability
- Latency
- Status Code

for each monitored website.

## CloudWatch Alarms

The project includes alarms for:

- Availability
- Latency
- Status Code

Example thresholds:

| Alarm | Threshold |
| ----------- | ----------- |
| Availability | < 1 |
| Latency | > 0.23 |
| Status Code | >= 400 |

## AWS CDK Commands

### Synth

```bash
cdk synth
```

### Deploy

```bash
cdk deploy
```

### Destroy

```bash
cdk destroy
```

## Testing

Lambda can be tested using the AWS Lambda Console.

Example test event:

```json
{
  "key1": "value1",
  "key2": "value2",
  "key3": "value3"
}
```

## Current Status

The core AWS monitoring infrastructure has been implemented.

The next step is to replace the current test values with real website measurements.

## Author

**Aiden**