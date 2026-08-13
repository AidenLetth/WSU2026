import boto3

#Put CloudWatch metric data
def putdatafunction(namespace, metricName, website, value):
    client = boto3.client('cloudwatch')
    return client.put_metric_data(
        Namespace=namespace,
        MetricData=[
            {
                'MetricName': metricName,
                'Dimensions': [
                    {
                        'Name': 'Website',
                        'Value': website
                    },
                ],
            'Value': value,
        }
    ]
)