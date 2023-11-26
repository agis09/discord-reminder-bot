import requests
import json
import os
import boto3
from datetime import datetime
from dotenv import load_dotenv
from boto3.dynamodb.conditions import Key, Attr


def lambda_handler(event, context):
    load_dotenv()

    date = int(
        f"{datetime.now().year}{str(datetime.now().month).zfill(2)}{str(datetime.now().day).zfill(2)}"
    )
    throw_remind(date)

    return {"statusCode": 200, "body": json.dumps("success")}


def get_records(**kwargs):
    dynamodb_resource = boto3.resource("dynamodb")
    TABLE_NAME = os.getenv("TABLE_NAME")
    while True:
        response = dynamodb_resource.Table(TABLE_NAME).scan(**kwargs)
        for item in response["Items"]:
            yield item
        if "LastEvaluatedKey" not in response:
            break
        kwargs.update(ExclusiveStartKey=response["LastEvaluatedKey"])


def throw_remind(date: int):
    options = {
        "FilterExpression": Attr("ymd").eq(date),
    }

    URL = os.getenv("WEBHOOK_URL")
    headers = {"Content-Type": "application/json"}

    for record in get_records(**options):
        response = requests.post(
            URL,
            data=json.dumps(
                {
                    "content": f"{record['content']} <@{record['mention']}>",
                    "username": "tester",
                }
            ),
            headers=headers,
        )
        print(f"👉 remind: {record['content']}, res: {response}")


# if __name__ == "__main__":
#     main()
