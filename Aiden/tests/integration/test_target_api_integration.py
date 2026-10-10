import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "resources"))
import target_api 

class FakeTable:
    def __init__(self):
        self.items = {}
    
    #create
    def put_item(
        self,
        Item,
        ConditionExpression=None
    ):
        self.items[Item["target_id"]] = Item

        return {
            "ResponseMetadata": {
                "HTTPStatusCode": 200
            }
        }
    
    #read one 
    def get_item(self, Key):
        target_id = Key["target_id"]

        if target_id in self.items:
            return {
                "Item": self.items[target_id]
            }

        return {}

#fake boto3 dynamodb resource:
class FakeDynamoDBResource:
    def __init__(self, table):
        self.table = table

    # Simulate boto3.resource("dynamodb").Table(...)
    def Table(self, table_name):
        return self.table
    

#Test target_api + get_table + boto3 dynamodb flow
def test_target_api_dynamodb_integration(monkeypatch):
    fake_table = FakeTable()
    fake_resource = FakeDynamoDBResource(
        fake_table
    )
    #environment 
    monkeypatch.setenv(
        "TARGETS_TABLE_NAME",
        "TestCrawlerTargetsTable")
    #replace boto3 dyanmodb resource, keep real get_table()
    monkeypatch.setattr(
        target_api.boto3,
        "resource",
        lambda service_name: fake_resource)
    
    #Create target
    create_event = {
        "httpMethod": "POST",
        "pathParameters": None,
        "body": json.dumps({
            "target_id": "google",
            "name": "Google",
            "url": "https://www.google.com"
        })
    }
    create_response = target_api.lambda_handler(
        create_event,
        None
    )
    create_body = json.loads(
        create_response["body"]
    )

    assert create_response["statusCode"] == 201
    assert (
        create_body["target"]["target_id"]
        == "google")
    assert "write_time_ms" in create_body

    #read target
    read_event = {
        "httpMethod": "GET",
        "pathParameters": {
            "target_id": "google"
        }
    }
    read_response = target_api.lambda_handler(
        read_event,
        None
    )
    read_body = json.loads(
        read_response["body"]
    )

    assert read_response["statusCode"] == 200
    assert (
        read_body["target"]["name"]
        == "Google"
    )
    assert "read_time_ms" in read_body

    
