import json 
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "resources"))
import target_api

class FakeTable:
    def __init__(self): self.items = {}
    def put_item(self,Item, ConditionExpression=None):
        self.items[Item["target_id"]] = Item
        return{
            "ResponseMetadata": {
                "HTTPStatusCode": 200
            }}
    def get_item(self,Key):
        target_id = Key["target_id"]
        if target_id in self.items:
            return {
                "Item": self.items[target_id]
            }
        return {}
    
#Test 1: POST/ targets creates a new target
def test_create_target(monkeypatch):
    fake_table = FakeTable()
    #fake table
    monkeypatch.setattr(
        target_api,
        "get_table",
        lambda: fake_table
        )
    event ={
        "httpMethod": "POST",
        "pathParameters": None,
        "body": json.dumps({
            "target_id":"google",
            "name": "Google",
            "url": "https://www.google.com"
            })
        }
    response = target_api.lambda_handler(
        event, 
        None
        )
    body = json.loads(response["body"])

    assert response ["statusCode"] == 201
    assert body["target"]["target_id"] == "google"
    assert body["target"]["name"] == "Google"
    assert body["target"]["url"] == "https://www.google.com"
    assert "write_time_ms" in body

#Test 2: GET /targets/{target_id} reads a target
def test_read_target(monkeypatch):
    fake_table = FakeTable()
    fake_table.items["google"] ={
        "target_id": "google",
        "name": "Google",
        "url": "https://www.google.com"
        }
    monkeypatch.setattr(
        target_api,
        "get_table",
        lambda: fake_table
        )
    event ={
        "httpMethod": "GET",
        "pathParameters": {
        "target_id": "google"
        }}
    response = target_api.lambda_handler(
        event,
        None
         )
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["target"]["target_id"] == "google"
    assert body["target"]["name"] == "Google"
    assert "read_time_ms" in body



