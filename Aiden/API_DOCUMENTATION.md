# Web Crawler CRUD API Documentation

## Overview

RESTful API for managing Web Crawler monitoring targets.

The API is built using Amazon API Gateway and AWS Lambda, with crawler targets stored in Amazon DynamoDB.

Users can create, read, update, and delete website targets without modifying the Web Crawler source code.

The API also measures DynamoDB read and write operation time in milliseconds.

---

## Base URL

```text
https://[api-id].execute-api.ap-southeast-2.amazonaws.com/prod/
```

The API ID may change when the infrastructure is destroyed and redeployed.

To find the Production API ID after deployment:

```bash
aws cloudformation describe-stack-resources \
  --stack-name ProdStage-AidenStack \
  --query "StackResources[?ResourceType=='AWS::ApiGateway::RestApi'].[LogicalResourceId,PhysicalResourceId]" \
  --output table
```

The target endpoint is:

```text
https://[api-id].execute-api.ap-southeast-2.amazonaws.com/prod/targets
```

---

## Authentication

The API is currently public and does not require authentication.

For a production system, API keys, IAM authentication, or another authentication method could be added.

---

## Endpoints

### 1. List All Targets

**GET** `/targets`

Returns all crawler targets currently stored in DynamoDB.

**Response 200 OK:**

```json
{
  "targets": [
    {
      "target_id": "google",
      "name": "Google",
      "url": "https://www.google.com"
    },
    {
      "target_id": "wsu",
      "name": "Western Sydney University",
      "url": "https://www.westernsydney.edu.au"
    }
  ],
  "read_time_ms": 10.42
}
```

`read_time_ms` shows the time required to read the data from DynamoDB.

**Example:**

```bash
curl https://[api-id].execute-api.ap-southeast-2.amazonaws.com/prod/targets
```

---

### 2. Create Target

**POST** `/targets`

Creates a new crawler target.

**Request Body:**

```json
{
  "target_id": "google",
  "name": "Google",
  "url": "https://www.google.com"
}
```

All three fields are required.

**Response 201 Created:**

```json
{
  "message": "Target created",
  "target": {
    "target_id": "google",
    "name": "Google",
    "url": "https://www.google.com"
  },
  "write_time_ms": 12.45
}
```

`write_time_ms` shows the time required to write the target to DynamoDB.

**Response 400 Bad Request:**

```json
{
  "message": "target_id, name and url are required"
}
```

**Response 409 Conflict:**

```json
{
  "message": "Target already exists"
}
```

**Example:**

```bash
curl -X POST \
  https://[api-id].execute-api.ap-southeast-2.amazonaws.com/prod/targets \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": "google",
    "name": "Google",
    "url": "https://www.google.com"
  }'
```

---

### 3. Get Single Target

**GET** `/targets/{target_id}`

Retrieves one crawler target using its `target_id`.

**Path Parameter:**

- `target_id` - ID of the crawler target.

Example:

```text
GET /targets/google
```

**Response 200 OK:**

```json
{
  "target": {
    "target_id": "google",
    "name": "Google",
    "url": "https://www.google.com"
  },
  "read_time_ms": 8.72
}
```

**Response 404 Not Found:**

```json
{
  "message": "Target not found",
  "read_time_ms": 7.31
}
```

**Example:**

```bash
curl \
  https://[api-id].execute-api.ap-southeast-2.amazonaws.com/prod/targets/google
```

---

### 4. Update Target

**PUT** `/targets/{target_id}`

Updates the name and URL of an existing crawler target.

**Path Parameter:**

- `target_id` - ID of the target to update.

Example:

```text
PUT /targets/google
```

**Request Body:**

```json
{
  "name": "Google Search",
  "url": "https://www.google.com"
}
```

Both `name` and `url` are required by the current implementation.

**Response 200 OK:**

```json
{
  "message": "Target updated",
  "target": {
    "target_id": "google",
    "name": "Google Search",
    "url": "https://www.google.com"
  },
  "write_time_ms": 10.32
}
```

**Response 400 Bad Request:**

```json
{
  "message": "name and url are required"
}
```

**Response 404 Not Found:**

```json
{
  "message": "Target not found"
}
```

**Example:**

```bash
curl -X PUT \
  https://[api-id].execute-api.ap-southeast-2.amazonaws.com/prod/targets/google \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Google Search",
    "url": "https://www.google.com"
  }'
```

---

### 5. Delete Target

**DELETE** `/targets/{target_id}`

Deletes an existing crawler target from DynamoDB.

**Path Parameter:**

- `target_id` - ID of the target to delete.

Example:

```text
DELETE /targets/google
```

**Response 200 OK:**

```json
{
  "message": "Target deleted",
  "target": {
    "target_id": "google",
    "name": "Google Search",
    "url": "https://www.google.com"
  },
  "write_time_ms": 9.54
}
```

**Response 404 Not Found:**

```json
{
  "message": "Target not found",
  "write_time_ms": 5.82
}
```

**Example:**

```bash
curl -X DELETE \
  https://[api-id].execute-api.ap-southeast-2.amazonaws.com/prod/targets/google
```

---

## Error Handling

The API returns JSON responses when requests cannot be completed.

Example:

```json
{
  "message": "Target not found"
}
```

### Common HTTP Status Codes

- `200 OK` - Request completed successfully.
- `201 Created` - Target created successfully.
- `400 Bad Request` - Invalid request or missing fields.
- `404 Not Found` - Target does not exist.
- `409 Conflict` - Target already exists.
- `405 Method Not Allowed` - HTTP method is not supported.
- `500 Internal Server Error` - Unexpected server-side error.

---

## DynamoDB Performance Measurement

The API measures DynamoDB read and write execution time using Python:

```python
time.perf_counter()
```

For a read operation:

```python
start_time = time.perf_counter()

response = table.get_item(
    Key={
        "target_id": target_id
    }
)

read_time = (
    time.perf_counter() - start_time
) * 1000
```

Read operations return:

```text
read_time_ms
```

Write operations return:

```text
write_time_ms
```

The values are measured in milliseconds.

This allows DynamoDB read and write performance to be included in API testing and monitoring.

---

## Integration with the Web Crawler

When a crawler target is created, updated, or deleted through the API:

1. API Gateway receives the REST request.
2. The CRUD Lambda in `resources/target_api.py` processes the request.
3. The CRUD Lambda reads or writes the DynamoDB crawler target table.
4. The Web Crawler Lambda reads the current target list from DynamoDB.
5. EventBridge invokes the Web Crawler every five minutes.
6. The crawler sends HTTP requests to the current website targets.
7. Availability, Latency, and Response Size are published to CloudWatch.

The application flow is:

```text
User
 |
 v
API Gateway
 |
 v
CRUD Lambda
 |
 v
DynamoDB Targets Table
 |
 v
Web Crawler Lambda
 |
 v
Target Websites
 |
 v
CloudWatch
```

This allows the website monitoring list to be changed dynamically without modifying the Web Crawler source code.

---

## Example Workflow

Create a target:

```bash
curl -X POST \
  https://[api-id].execute-api.ap-southeast-2.amazonaws.com/prod/targets \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": "google",
    "name": "Google",
    "url": "https://www.google.com"
  }'
```

Read the target:

```bash
curl \
  https://[api-id].execute-api.ap-southeast-2.amazonaws.com/prod/targets/google
```

Update the target:

```bash
curl -X PUT \
  https://[api-id].execute-api.ap-southeast-2.amazonaws.com/prod/targets/google \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Google Search",
    "url": "https://www.google.com"
  }'
```

Delete the target:

```bash
curl -X DELETE \
  https://[api-id].execute-api.ap-southeast-2.amazonaws.com/prod/targets/google
```

---

## Testing

The Applied Project adds automated tests for the CRUD API and DynamoDB interaction.

The additional tests include:

```text
2 Unit Tests
1 Functional Test
1 Integration Test
```

The functional test verifies the complete CRUD workflow:

```text
POST
 |
 v
GET
 |
 v
PUT
 |
 v
DELETE
```

The integration test verifies the interaction between the API business logic, `get_table()`, Boto3 DynamoDB resource, and the DynamoDB table interface.

The complete project test suite currently contains:

```text
25 Tests
25 Passed
```

Run all tests using:

```bash
python -m pytest
```