import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2] / "resources")
)

import target_api


class FakeTable:
    def __init__(self):
        self.items = {}
    
    #CREATE
    def put_item(self,
        Item,
        ConditionExpression=None):
        self.items[Item["target_id"]] = Item

        return{
            "ResponseMetadata": {
                "HTTPStatusCode": 200
        }}
    
    #Read one
    def get_item(self, Key):
        target_id = Key["target_id"]

        if target_id in self.items:
            return {
                "Item": self.items[target_id]
            }

        return {}
    
    #read all
    def scan(self, ExclusiveStartKey=None):
        return {
            "Items": list(self.items.values())
        }
    
    #Update
    def update_item(
        self,
        Key,
        UpdateExpression=None,
        ExpressionAttributeNames=None,
        ExpressionAttributeValues=None,
        ConditionExpression=None,
        ReturnValues=None):
    
     target_id = Key["target_id"]
     self.items[target_id]["name"] = (
            ExpressionAttributeValues[":name"]
        )

     self.items[target_id]["url"] = (
            ExpressionAttributeValues[":url"]
        )
     return {
            "Attributes": self.items[target_id]
        }

    #Delete
    def delete_item(
        self,
        Key,
        ReturnValues=None):
    
     target_id = Key["target_id"]

     if target_id in self.items:
            deleted_item = self.items.pop(target_id)

            return {
                "Attributes": deleted_item
            }

     return {}
    
#Test follow workdlow: POST - GET- PUT - DELETE
def test_full_crud_workflow(monkeypatch):
    fake_table = FakeTable()
    #fake table:
    monkeypatch.setattr(
        target_api,
        "get_table",
        lambda: fake_table
    )
    
    #CREATE (POST)/ targets
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
    assert create_body["target"]["target_id"] == "google"
    assert "write_time_ms" in create_body

    #READ (GET) /targets/google
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
    assert read_body["target"]["name"] == "Google"
    assert "read_time_ms" in read_body

    #UPDATE (PUT) /targets/google
    update_event = {
        "httpMethod": "PUT",
        "pathParameters": {
            "target_id": "google"
        },
        "body": json.dumps({
            "name": "Google Search",
            "url": "https://www.google.com"
        })
    }

    update_response = target_api.lambda_handler(
        update_event,
        None
    )
    update_body = json.loads(
        update_response["body"]
    )

    assert update_response["statusCode"] == 200
    assert (
        update_body["target"]["name"]
        == "Google Search"
    )
    assert "write_time_ms" in update_body

    #DELETE /targets/google
    delete_event = {
        "httpMethod": "DELETE",
        "pathParameters": {
            "target_id": "google"
        }
    }
    delete_response = target_api.lambda_handler(
        delete_event,
        None
    )
    delete_body = json.loads(
        delete_response["body"]
    )

    assert delete_response["statusCode"] == 200
    assert (
        delete_body["target"]["target_id"]
        == "google"
    )
    assert "write_time_ms" in delete_body

    # Confirm the target was deleted
    assert "google" not in fake_table.items





