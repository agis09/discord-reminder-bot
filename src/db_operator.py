import boto3
import time
import os
from boto3.dynamodb.conditions import Attr

TABLE_NAME = os.getenv("TABLE_NAME")

dynamodb_client = boto3.client("dynamodb")
dynamodb_resource = boto3.resource("dynamodb")


def put():
    key = int(time.time())
    item = {
        "TableName": TABLE_NAME,
        "Item": {
            "reminder_id": {"N": str(key)},
            "ymd": {"N": "20231120"},
            "mention": {"S": "usr"},
            "content": {"S": "test"},
        },
    }
    dynamodb_client.put_item(**item)


def get_records(**kwargs):
    while True:
        response = dynamodb_resource.Table(TABLE_NAME).scan(**kwargs)
        for item in response["Items"]:
            yield item
        if "LastEvaluatedKey" not in response:
            break
        kwargs.update(ExclusiveStartKey=response["LastEvaluatedKey"])


def scan_remind(date):
    options = {
        "FilterExpression": Attr("ymd").eq(date),
    }
    records = get_records(**options)

    for record in records:
        print(record["reminder_id"], record["ymd"], record["content"])


def delete(date):
    options = {
        "FilterExpression": Attr("ymd").lt(date),
    }
    records = get_records(**options)

    for record in records:
        print(f'delete: {record["reminder_id"]}, {record["ymd"]}, {record["content"]}')
        dynamodb_resource.Table(TABLE_NAME).delete_item(
            Key={"reminder_id": record["reminder_id"], "ymd": record["ymd"]}
        )


if __name__ == "__main__":
    # put()
    # scan_remind(202311219)
    delete(20241231)
