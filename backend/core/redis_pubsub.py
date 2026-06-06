import json
from typing import Any, Dict

import redis

from core.config import configs
from schemas.tasks import TaskNotificationPayload

_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(configs.REDIS_URL, decode_responses=True)
    return _redis_client


def user_channel(user_id: int) -> str:
    return f"user:{user_id}:notifications"


def publish_task_notification(user_id: int, payload: TaskNotificationPayload) -> None:
    client = get_redis_client()
    client.publish(user_channel(user_id), payload.model_dump_json())


def publish_task_notification_dict(user_id: int, data: Dict[str, Any]) -> None:
    client = get_redis_client()
    client.publish(user_channel(user_id), json.dumps(data, ensure_ascii=False))
