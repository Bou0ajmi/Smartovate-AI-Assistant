import boto3
import uuid
from datetime import datetime, timezone
from config import USER_TABLE_NAME
from config import REGION_NAME


def _table():
    dynamodb = boto3.resource("dynamodb", region_name=REGION_NAME)
    return dynamodb.Table(USER_TABLE_NAME)


def create_thread(user_id: str, title: str = "New conversation") -> str:
    """Creates a new thread for a user and returns the new thread_id."""
    thread_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    _table().put_item(Item={
        "user_id": user_id,
        "thread_id": thread_id,
        "title": title,
        "created_at": now,
        "last_active_at": now,
        "messages": [],
    })
    return thread_id


def get_thread(user_id: str, thread_id: str):
    """Returns the thread record if it belongs to this user, else None."""
    response = _table().get_item(Key={"user_id": user_id, "thread_id": thread_id})
    return response.get("Item")


def list_threads(user_id: str) -> list:
    """Returns all threads belonging to a user, most recent first."""
    response = _table().query(
        KeyConditionExpression="user_id = :uid",
        ExpressionAttributeValues={":uid": user_id},
    )
    items = response.get("Items", [])
    return sorted(items, key=lambda x: x["last_active_at"], reverse=True)


def get_messages(user_id: str, thread_id: str) -> list:
    """Returns the stored message history for a thread, or [] if none/not found."""
    thread = get_thread(user_id, thread_id)
    if thread is None:
        return []
    return thread.get("messages", [])


def append_message(user_id: str, thread_id: str, role: str, content: str):
    """Appends one message to the thread's stored history and updates last_active_at."""
    now = datetime.now(timezone.utc).isoformat()
    _table().update_item(
        Key={"user_id": user_id, "thread_id": thread_id},
        UpdateExpression="SET messages = list_append(if_not_exists(messages, :empty), :new_msg), last_active_at = :now",
        ExpressionAttributeValues={
            ":new_msg": [{"role": role, "content": content, "timestamp": now}],
            ":empty": [],
            ":now": now,
        },
    )


def touch_thread(user_id: str, thread_id: str):
    """Updates last_active_at whenever a thread is used."""
    now = datetime.now(timezone.utc).isoformat()
    _table().update_item(
        Key={"user_id": user_id, "thread_id": thread_id},
        UpdateExpression="SET last_active_at = :now",
        ExpressionAttributeValues={":now": now},
    )