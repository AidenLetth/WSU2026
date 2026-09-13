import json
import os
import uuid
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ["DYNAMODB_TABLE_NAME"])
def lambda_handler(event, context):
    print(event)
    for record in event ["Records"]:
        message = json.loads(record["Sns"]["Message"])
    table.put_item(Item={
           "alarm_id": str(uuid.uuid4()),
           "alarm_name": message.get("AlarmName","Unknown"),
            "new_state_value": message.get("NewStateValue","Unknown"),
            "new_state_reason": message.get("NewStateReason","Unknown"),
            "timestamp": datetime.utcnow().isoformat()
        })
    return {
        "statusCode": 200
    }

