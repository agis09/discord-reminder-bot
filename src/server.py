import os
from flask import Flask, jsonify, request
from discord_interactions import verify_key_decorator
from asgiref.wsgi import WsgiToAsgi
from mangum import Mangum
import datetime
import boto3
import time

DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY")

TABLE_NAME = os.getenv("TABLE_NAME")

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)
handler = Mangum(asgi_app)


@app.route("/", methods=["POST"])
async def interactions():
    # print(f"👉 Request: {request.json}")
    raw_request = request.json
    return interact(raw_request)


@verify_key_decorator(DISCORD_PUBLIC_KEY)
def interact(raw_request):
    if raw_request["type"] == 1:  # PING
        response_data = {"type": 1}  # PONG
    else:
        data = raw_request["data"]
        command_name = data.get("name", None)

        if command_name:
            target_id = data["target_id"]
            content = data["resolved"]["messages"][target_id]["content"]
            response_data = {
                "type": 4,
                "data": {
                    "content": f"I'll remind `{content}`. \nSet the reminder month.",
                    "components": [
                        {
                            "type": 1,
                            "components": [
                                {
                                    "type": 3,
                                    "custom_id": "month",
                                    "options": [
                                        {"label": f"{i}月", "value": f"{i}"}
                                        for i in range(1, 13)
                                    ],
                                }
                            ],
                        }
                    ],
                },
            }
        elif data["custom_id"] == "month":
            month = int(data["values"][0])
            parsed_content = contents_parser(raw_request["message"]["content"])
            remind_content = parsed_content[0]

            response_data = {
                "type": 7,
                "data": {
                    "content": f"I'll remind `{remind_content}` in `{month}`月. \nSelect the reminder days range.",
                    "components": [
                        {
                            "type": 1,
                            "components": [
                                {
                                    "type": 3,
                                    "custom_id": "days_range",
                                    "options": [
                                        {"label": "1st to 15th", "value": "1"},
                                        {"label": "16th to 31st", "value": "2"},
                                    ],
                                }
                            ],
                        }
                    ],
                },
            }
        elif data["custom_id"] == "days_range":
            parsed_content = contents_parser(raw_request["message"]["content"])
            remind_content = parsed_content[0]
            month = parsed_content[1]
            response_data = days_select_components(
                data["values"][0], remind_content, month
            )

        else:
            day = data["values"][0]
            parsed_content = contents_parser(raw_request["message"]["content"])
            remind_content = parsed_content[0]
            month = parsed_content[1]
            response_data = {
                "type": 7,
                "data": {
                    "content": "",
                    "components": [
                        {
                            "type": 1,
                            "components": [
                                {
                                    "type": 3,
                                    "custom_id": "finish_selection",
                                    "options": [
                                        {"label": "label1", "value": "1"},
                                        {"label": "label2", "value": "2"},
                                    ],
                                    "disabled": "true",
                                }
                            ],
                        }
                    ],
                },
            }

            user = raw_request["message"]["interaction"]["user"]["id"]

            content = regist_reminder(remind_content, month, day, user)
            response_data["data"]["content"] = content

        return jsonify(response_data)


def contents_parser(content: str) -> list[str]:
    contents_candidates = content.split("`")
    parsed = [(contents_candidates[1])]
    if len(contents_candidates) > 4:
        parsed.append(contents_candidates[3])
    return parsed


def days_select_components(days_range: str, remind_content: str, month: str) -> dict:
    days: range = range(1, 15) if days_range == "1" else range(16, 32)
    res = {
        "type": 7,
        "data": {
            "content": f"I'll remind `{remind_content}` in `{month}`月. \nSet the reminder day.",
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 3,
                            "custom_id": "day",
                            "options": [
                                {"label": f"{i}日", "value": f"{i}"} for i in days
                            ],
                        }
                    ],
                }
            ],
        },
        "disabled": True,
    }
    return res


def regist_reminder(content: str, month: str, day: str, user: str) -> str:
    remind_year = datetime.datetime.now().year
    this_month = datetime.datetime.now().month
    if this_month < int(month):
        remind_year += 1
    if (
        (month in ["4", "6", "9", "11"] and day == "31")
        or (month == "2" and remind_year % 4 != 0 and int(day) > 28)
        or (month == "2" and remind_year % 4 == 0 and int(day) > 29)
    ):
        res = f"You set invalid date!!\n `{remind_year}`年 `{month}`月 `{day}`日 is not exist!!"
    else:
        res = f"I'll remind {content} in `{remind_year}`年 `{month}`月 `{day}`日 19:00."

    dynamodb_client = boto3.client("dynamodb")
    DB_key = int(time.time())
    item = {
        "TableName": TABLE_NAME,
        "Item": {
            "reminder_id": {"N": str(DB_key)},
            "ymd": {"N": f"{remind_year}{month.zfill(2)}{day.zfill(2)}"},
            "mention": {"S": f"{user}"},
            "content": {"S": f"{content}"},
        },
    }
    dynamodb_client.put_item(**item)
    print(f"👉 insert: {item}")

    return res


if __name__ == "__main__":
    app.run(debug=True)
