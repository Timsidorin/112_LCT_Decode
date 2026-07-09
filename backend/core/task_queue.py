"""Celery-клиент"""

from celery import Celery

from core.config import configs

_publisher: Celery | None = None


def get_task_publisher() -> Celery:
    global _publisher
    if _publisher is None:
        _publisher = Celery(
            "events_knastu_publisher",
            broker=configs.CELERY_BROKER_URL,
        )
        _publisher.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
        )
    return _publisher


def enqueue_process_training_video(task_id: str) -> None:
    get_task_publisher().send_task(
        "worker.tasks.process_training_video_task",
        args=[task_id],
    )

def enqueue_process_training_pdf(task_id: str) -> None:
    get_task_publisher().send_task(
        "worker.tasks.process_training_pdf_task",
        args=[task_id],
    )
