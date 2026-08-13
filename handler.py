import json
import base64
import logging
import uuid

from src.agent.get_agent import get_agent
from src.memory.thread_store import create_thread, get_thread, append_message

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    try:
        raw_body = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            raw_body = base64.b64decode(raw_body).decode("utf-8")
        body = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError, base64.binascii.Error) as e:
        logger.error(f"Invalid request body: {e}")
        return _response(400, {"error": "Malformed JSON body"})

    user_id = body.get("user_id")
    if not user_id or not isinstance(user_id, str):
        return _response(400, {"error": "Missing or invalid 'user_id'"})

    query = body.get("query")
    if not query or not isinstance(query, str):
        return _response(400, {"error": "Missing or invalid 'query'"})

    thread_id = body.get("thread_id")
    try:
        if not thread_id:
            thread_id = create_thread(user_id, title=query[:50])
        else:
            thread = get_thread(user_id, thread_id)
            if thread is None:
                return _response(403, {"error": "Thread not found or access denied"})
    except Exception as e:
        logger.error(f"Thread resolution failed: {e}")
        return _response(500, {"error": "Thread resolution failed"})

    try:
        append_message(user_id, thread_id, "user", query)
    except Exception as e:
        logger.error(f"Failed to log user message: {e}")

    try:
        agent = get_agent()
    except Exception as e:
        logger.error(f"Agent initialization failed: {e}")
        return _response(500, {"error": "Agent initialization failed"})

    try:
        result = agent.invoke(thread_id=thread_id, user_input=query)
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return _response(500, {"error": "Agent execution failed", "details": str(e)})

    try:
        append_message(user_id, thread_id, "assistant", result)
    except Exception as e:
        logger.error(f"Failed to log assistant message: {e}")

    return _response(200, {"thread_id": thread_id, "response": result})


def _response(status_code, body_dict):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body_dict),
    }