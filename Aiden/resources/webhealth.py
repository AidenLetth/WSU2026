import CWdata as cw
import constants

def lambda_handler(event, context):
    print(event)

    # Simulate website health check data
    website_health = {
        "https://www.ralphlauren.com": {
            "availability": 1,  # 1 for available, 0 for unavailable
            "latency": 0.35,  # in seconds
            "responseSize": 180  # in bytes
        },
        "https://www.google.com": {
            "availability": 1,
            "latency": 0.2,
            "responseSize": 195
        },
        "https://www.westernsydney.edu.au": {
            "availability": 0,
            "latency": 0.5,
            "responseSize": 300
        }
    }

    responses = []

    # Simulate website health check data
    for website in constants.WEBSITES:   #loop through the list of websites and send the data to CloudWatch
       availability = website_health[website]["availability"]
       latency = website_health[website]["latency"]
       responseSize = website_health[website]["responseSize"]
       # Send the data to CloudWatch using the putdatafunction
       #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.put_metric_data
       response1 = cw.putdatafunction(constants.namespace, constants.metricAvailability, website, availability)
       response2 = cw.putdatafunction(constants.namespace, constants.metricLatency, website, latency)
       response3 = cw.putdatafunction(constants.namespace, constants.metricResponseSize, website, responseSize)
       responses.append({
        "website": website,
        "availability": response1,
        "latency": response2,
        "response_size": response3
        })
    return responses