import CWdata as cw
import constants
import urllib.request
import urllib.error
import time
import boto3
import os

def get_target():
    table_name=os.environ.get("TARGETS_TABLE_NAME")

    #fallback for local/unit tests
    if not table_name:
        return constants.WEBSITES
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    
    start_time =time.perf_counter()
    response = table.scan()
    read_time= (time.perf_counter() - start_time)*1000
    print(f"DynamoDB read time :{read_time:.2f}ms")

    return[
        item["url"]
        for item in response.get("Items", [])
        if "url" in item
    ]


def lambda_handler(event, context):
    print(event)
    responses = []
     
    websites = get_target()
    for website in websites:
        availability = 0
        latency = 0
        responseSize = 0
        try:
            #Create a real HTTP request to the website and measure the response time and size
            #https://docs.python.org/3/library/urllib.request.html#urllib.request.urlopen
            request = urllib.request.Request(
            website,
            headers={"User-Agent": "Mozilla/5.0 WebHealthMonitor"}
            )

            #Start measuring response time
            start_time = time.perf_counter() #time.perf_counter() is used to measure the time taken for the request to complete #https://docs.python.org/3/library/time.html#time.perf_counter
            with urllib.request.urlopen(request, timeout=10) as response:
                #Read real websites 
                data=response.read()
                
                #Calculate real latency 
                latency = (time.perf_counter() - start_time)

                #Availability =1 if the website is available, 0 if not
                availability = 1

                #Real response size in bytes
                responseSize = len(data)
                
        except urllib.error.HTTPError as e:
            latency = (time.perf_counter() - start_time)
            availability = 0
            try:
                responseSize = len(e.read())
            except Exception:
                responseSize = 0
            
            print(f"HTTPError for {website}: {e.code} - {e.reason}")

        except Exception as error:
            latency = (time.perf_counter() - start_time)
            availability = 0
            responseSize = 0
            print(f"Error for {website}: {error}")

        #print real values to CW
        print(
            f"Website: {website} | "
            f"Availability: {availability} | "
            f"Latency: {latency:.3f} seconds | "
            f"Response Size: {responseSize} bytes"
        )

        # Send the data to CloudWatch using the putdatafunction
        #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.put_metric_data
        response1 = cw.putdatafunction(constants.namespace, constants.metricAvailability, website, availability)
        response2 = cw.putdatafunction(constants.namespace, constants.metricLatency, website, latency)
        response3 = cw.putdatafunction(constants.namespace, constants.metricResponseSize, website, responseSize)
        responses.append({
            "website": website,
            "availability": availability,
            "latency": latency,
            "response_size": responseSize
        })
    return responses