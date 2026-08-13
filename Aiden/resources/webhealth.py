import CWdata as cw
import constants

def lambda_handler(event, context):
    print(event)

    # Simulate website health check data
    availability = 1 #1 for available, 0 for unavailable
    latency = 0.23 # in seconds
    statusCode = 200 #200 for success

    responses = []

    # Simulate website health check data
    for website in constants.WEBSITES:   #loop through the list of websites and send the data to CloudWatch
       response1 = cw.putdatafunction(constants.namespace, constants.metricAvailability, website, availability)
       response2 = cw.putdatafunction(constants.namespace, constants.metricLatency, website, latency)
       response3 = cw.putdatafunction(constants.namespace, constants.metricStatusCode, website, statusCode)
       responses.append({
        "website": website,
        "availability": response1,
        "latency": response2,
        "status_code": response3
        })
    return responses