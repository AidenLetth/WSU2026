import boto3
import json
import os
import time
from botocore.exceptions import ClientError


# Get the DynamoDB table using the table name
def get_table():
    table_name = os.environ["TARGETS_TABLE_NAME"]
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(table_name)

#standard response 
def create_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }

#main lambda handler 
def lambda_handler(event, context):
    print(event)
    table = get_table()
    method = event.get("httpMethod","")
    #target_id 
    path_parameters = event.get("pathParameters") or {}
    target_id = path_parameters.get("target_id")

    #Create
    #POST/ targets
    #add new website target to DynamoDB
    if method == "POST":
        try:
            body= json.loads(event.get("body","{}"))
        except json.JSONDecodeError:
            return create_response(
                400, #bad request
                {
                    "message": "Invalid JSON body"
                }
            )
        
        target_id = body.get("target_id")
        name = body.get("name")
        url = body.get("url")

        if not target_id or not name or not url:
            return create_response(
                400, ##
                {
                    "message": 
                    "target_id, name and url are required"
                }
            )
        
        #DynamoDB item
        item ={
            "target_id": target_id,
            "name": name,
            "url": url
        }

        try:
            start_time = time.perf_counter()
            table.put_item(
                Item=item,
                ConditionExpression=(
                "attribute_not_exists(target_id)"
            )
            )
            write_time = (time.perf_counter() - start_time)*1000
        except ClientError as error:
                if (
                    error.response["Error"]["Code"] == "ConditionalCheckFailedException"
                ):
                    return create_response(
                        409, #duplicate target
                        {
                            "message": "Target already exists"
                        }
                    )
            
                raise 
        print(
            f"DynamoDB write time :{write_time:.2f}ms"      
        )
        return create_response(
                    201, #successfully created 
                    {
                        "message": "Target created",
                        "target": item,
                        "write_time_ms": round(write_time, 2)
                    }
                )
    
    #Read one
    #GET/targets/ {target_id}
    #Get one website target from DynamoDB 

    if method == "GET" and target_id:
        start_time = time.perf_counter()
        response = table.get_item(
            Key={"target_id": target_id}
        )
        read_time =(time.perf_counter() - start_time)*1000
        print(f"DynamoDB read time: "
              f"{read_time:.2f}ms"
        )
        item = response.get("Item")
        #return 404 if item not found
        if not item:
            return create_response(
                404,
                {
                    "message": "Target not found",
                    "read_time_ms": round(read_time, 2)
                }
            )
        return create_response(
            200,
            {
                "target": item,
                "read_time_ms": round(read_time, 2)
            }
        )
    #READ ALL/  GET
    if method == "GET":
        start_time = time.perf_counter()
        response = table.scan()
        items = response.get("Items", [])
        #contiune scanning, need more than one page 
        while "LastEvaluatedKey" in response:
            response = table.scan(
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))
        read_time = (time.perf_counter() - start_time)*1000
        print(f"DynamoDB read time: "
               f"{read_time:.2f}ms")
        return create_response(
            200,
            {
                "targets": items,
                "read_time_ms": round(read_time, 2)
            }
        )
    
    #UPDATE / PUT /targets/ {target_id}: Update an existing website target
    if method == "PUT" and target_id:
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return create_response(
                400,
                {
                    "message": "Invalid JSON body"
                }
            )
        name = body.get("name")
        url = body.get("url")

        if not name or not url:
            return create_response(
                400,
                {
                    "message": 
                    "name and url are required"
                }
            )
        try:
            start_time = time.perf_counter()
            response = table.update_item(
                Key={"target_id": target_id},
                #update website name and url
                UpdateExpression=(
                    "SET #target_name = :name, "
                    "#target_url = :url"
                ),
                ExpressionAttributeNames={
                    "#target_name": "name",
                    "#target_url": "url"
                },
                ExpressionAttributeValues={
                    ":name": name,
                    ":url": url
                },

                ConditionExpression=("attribute_exists(target_id)"),
                ReturnValues="ALL_NEW"
            )
            write_time = (time.perf_counter() - start_time)*1000
        except ClientError as error:
            if (
                error.response["Error"]["Code"] == "ConditionalCheckFailedException"
            ):
                return create_response(
                    404,
                    {
                        "message": "Target not found"
                    }
                )
            raise
        
        updated_item = response.get("Attributes")
        print(f"DynamoDB write time: "
              f"{write_time:.2f}ms")
        return create_response(
            200,
            {
                "message": "Target updated",
                "target": response["Attributes"],
                "write_time_ms": round(write_time, 2)
            }
        )
    
    #DELETE /targets/ {target_id}: Delete an existing website target
    if method == "DELETE" and target_id:
            start_time = time.perf_counter()
            response = table.delete_item(
                Key={"target_id": target_id},
                ReturnValues="ALL_OLD"
            )
            write_time = (time.perf_counter() - start_time)*1000

    if "Attributes" not in response:
                return create_response(
                    404,
                    {
                        "message": "Target not found",
                        "write_time_ms": round(write_time, 2)
                    }
                )
    print(f"DynamoDB write time: "
              f"{write_time:.2f}ms")
    return create_response(
            200,
            {
                "message": "Target deleted",
                "target": response["Attributes"],
                "write_time_ms": round(write_time, 2)
            }
        )
    #return 405 when the request method does not mach any CRUD operation
    return create_response(
        405,
        {
            "message": "Method not allowed"
        }
    )