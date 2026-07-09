import time

from core.celery_app import celery_app
from core.config import configs
from core.logging_config import logger
from core.redis_pubsub import publish_task_notification
from models.tasks import TaskStatus, TaskType
from schemas.tasks import TaskNotificationPayload
from services.external_services.s3_service import S3Service
from worker.db import get_task, update_task_status
from worker.task_runtime import run_worker_task


def _notify(user_id: int, task_id: str, status: str, **kwargs) -> None:
    payload = TaskNotificationPayload(
        task_id=task_id,
        status=status,
        progress=kwargs.get("progress", 0),
        result_url=kwargs.get("result_url"),
        error_message=kwargs.get("error_message"),
        message=kwargs.get("message"),
    )
    publish_task_notification(user_id, payload)


def _process_file_content(
    file_bytes: bytes,
    task_type: str,
    original_filename: str,
) -> bytes:
    """
    Заглушка тяжёлой обработки. В продакшене здесь FFmpeg / PyMuPDF и т.д.
    """
    time.sleep(2)
    if task_type == TaskType.PDF_PROCESSING.value:
        return file_bytes
    return file_bytes


@celery_app.task(name="worker.tasks.process_media_task", bind=True, max_retries=2)
def process_media_task(self, task_id: str) -> dict:
    task = get_task(task_id)
    if not task:
        logger.error("Задача {} не найдена", task_id)
        return {"ok": False, "error": "task_not_found"}

    user_id = task.user_id
    try:
        update_task_status(task_id, TaskStatus.PROCESSING.value, progress=10)
        _notify(
            user_id,
            task_id,
            TaskStatus.PROCESSING.value,
            progress=10,
            message="Обработка началась",
        )

        s3 = S3Service(session=None)  # type: ignore[arg-type]
        object_key = S3Service.key_from_public_url(
            task.file_url, s3.bucket_name, s3.endpoint_url
        )
        file_bytes = s3.download_bytes_sync(object_key)

        update_task_status(task_id, TaskStatus.PROCESSING.value, progress=40)
        _notify(
            user_id,
            task_id,
            TaskStatus.PROCESSING.value,
            progress=40,
            message="Файл загружен, идёт обработка",
        )

        result_bytes = _process_file_content(
            file_bytes,
            task.task_type,
            task.original_filename or "file.bin",
        )

        update_task_status(task_id, TaskStatus.PROCESSING.value, progress=80)
        _notify(
            user_id,
            task_id,
            TaskStatus.PROCESSING.value,
            progress=80,
            message="Сохранение результата",
        )

        result_key = s3.generate_result_object_key(
            user_id,
            task_id,
            task.original_filename or "result.bin",
        )
        result_url = s3.upload_bytes_sync(result_bytes, result_key)

        update_task_status(
            task_id,
            TaskStatus.COMPLETED.value,
            result_url=result_url,
            progress=100,
        )
        _notify(
            user_id,
            task_id,
            TaskStatus.COMPLETED.value,
            progress=100,
            result_url=result_url,
            message="Обработка завершена",
        )
        return {"ok": True, "task_id": task_id, "result_url": result_url}

    except Exception as exc:
        logger.exception("Ошибка обработки задачи {}", task_id)
        update_task_status(
            task_id,
            TaskStatus.FAILED.value,
            error_message=str(exc),
            progress=0,
        )
        _notify(
            user_id,
            task_id,
            TaskStatus.FAILED.value,
            error_message=str(exc),
            message="Ошибка обработки",
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30)
        raise exc


@celery_app.task(
    name="worker.tasks.process_training_video_task",
    bind=True,
    max_retries=1,
    time_limit=3600,
    soft_time_limit=3300,
)
def process_training_video_task(self, task_id: str) -> dict:
    """Фоновое создание шагов тренинга из видео (AI + S3)."""
    from worker.training_video import _run_training_video_async

    try:
        return run_worker_task(_run_training_video_async(task_id))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        raise exc


@celery_app.task(
    name="worker.tasks.process_training_pdf_task",
    bind=True,
    max_retries=1,
    time_limit=3600,
    soft_time_limit=3300,
)
def process_training_pdf_task(self, task_id: str) -> dict:
    """Фоновое создание шагов тренинга из PDF-инструкции (VLM + S3)."""
    from worker.training_pdf import _run_training_pdf_async

    try:
        return run_worker_task(_run_training_pdf_async(task_id))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        raise exc


@celery_app.task(name="worker.tasks.cleanup_expired_employee_accounts")
def cleanup_expired_employee_accounts() -> dict:
    from services.temp_employee_accounts_service import TempEmployeeAccountsService
    from worker.task_runtime import get_worker_session_factory

    async def _run() -> int:
        factory = get_worker_session_factory()
        async with factory() as session:
            service = TempEmployeeAccountsService(session)
            return await service.cleanup_expired()

    removed = run_worker_task(_run())
    logger.info("Removed {} expired temporary employee accounts", removed)
    return {"ok": True, "removed": removed}
