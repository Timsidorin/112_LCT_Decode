import io
import uuid
from typing import Any, Dict, List, Optional, Union

import requests
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile, status
from PIL import Image
from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.config import configs
from core.logging_config import logger
from models.trainings import (
    Tags,
    Training,
    TrainingPublication,
    TrainingStep,
    TypesAction,
)
from repositories.trainings_repository import TrainingRepository
from schemas.trainings import (
    PassageAnalyticsResponse,
    PassageCompleteRequest,
    PassageHistoryItemResponse,
    StepOrderUpdate,
    TrainingCreate,
    TrainingListResponse,
    TrainingResponse,
    TrainingStepCreate,
    TrainingStepResponse,
    TrainingStepUpdate,
    TrainingUpdate,
)
from services.external_services.s3_service import S3Service
from services.video_ai_service import VideoAIService
from services.pdf_ai_service import PdfAiService

# ID типа действия «Нажатие клавиши» — область хранит только metaKeywords
ACTION_TYPE_KEY_PRESS_ID = 6
ACTION_TYPE_INPUT_TEXT_ID = 5

_AREA_COORD_KEYS = frozenset({"x", "y", "width", "height", "actions"})


def _sanitize_area_for_action_type(
    area: Optional[Dict], action_type_id: Optional[int]
) -> Optional[Dict]:
    """Убирает metaText с шагов-кликов — иначе прохождение требует ввод текста."""
    if not isinstance(area, dict):
        return area
    if action_type_id == ACTION_TYPE_KEY_PRESS_ID:
        keywords = area.get("metaKeywords")
        return {
            "metaKeywords": keywords if isinstance(keywords, list) else [],
        }
    if action_type_id == ACTION_TYPE_INPUT_TEXT_ID:
        return area
    return {
        k: v
        for k, v in area.items()
        if k in _AREA_COORD_KEYS and v is not None
    }

# Ключи из VideoAIService → id в typesactions (create_initial_actions.py)
ACTION_TYPE_KEY_TO_ID = {
    "left_click": 1,
    "right_click": 2,
    "double_click": 3,
    "hover": 4,
    "text_input": 5,
    "key_chord": 6,
}


def _s3_object_key_from_public_url(image_url: str) -> Optional[str]:
    """Из публичного URL объекта (как после upload_file) получить S3 key."""
    from urllib.parse import unquote, urlparse

    raw = (image_url or "").strip()
    if not raw:
        return None
    ep = (configs.S3_ENDPOINT_URL or "").strip().rstrip("/")
    bn = (configs.S3_BUCKET_NAME or "").strip()
    if not ep or not bn or ep.startswith("S3_"):
        return None
    prefix = f"{ep}/{bn}/"
    if raw.startswith(prefix):
        return unquote(raw[len(prefix) :])
    try:
        path = unquote(urlparse(raw).path or "")
    except Exception:
        return None
    marker = f"/{bn}/"
    if marker in path:
        return path.split(marker, 1)[1]
    return None


class TrainingsService:
    def __init__(self, session: AsyncSession):
        self.repo = TrainingRepository(session)
        self.session = session

    async def create_training(self, training_data: TrainingCreate, creator_id: int):
        """Создание тренинга с тегами и шагами"""
        try:
            training_dict = training_data.model_dump(exclude={"steps", "tag_ids"})

            training = Training(**training_dict, creator_id=creator_id)

            if training_data.tag_ids:
                tags_result = await self.session.execute(
                    select(Tags).where(Tags.value.in_(training_data.tag_ids))
                )
                tags = tags_result.scalars().all()
                training.tags = list(tags)

            created_training = await self.repo.create(training)
            if not created_training:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Не удалось создать тренинг",
                )

            if training_data.steps:
                for step_data in training_data.steps:
                    step = await self.create_training_step(step_data)
                    step.training_uuid = created_training.uuid
                    await self.repo.create_training_step(step)

            await self.session.commit()

            created_training = await self.repo.get_by_uuid_with_relations(
                created_training.uuid
            )

            if created_training:
                return TrainingResponse.model_validate(created_training)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось получить созданный тренинг",
            )

        except HTTPException:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка создания тренинга: {str(e)}",
            )

    async def create_training_step(self, step_data: TrainingStepCreate) -> TrainingStep:
        """Создание объекта TrainingStep (без сохранения в БД)"""
        if step_data.action_type_id:
            action_type = await self.repo.get_action_type(step_data.action_type_id)
            if not action_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Тип действия с ID {step_data.action_type_id} не найден",
                )

            step_dict = step_data.model_dump(exclude={"action_type_id"})
            return TrainingStep(**step_dict, action_type=action_type)
        else:
            step_dict = step_data.model_dump(exclude={"action_type_id"})
            return TrainingStep(**step_dict)

    async def get_training(self, training_uuid: UUID4) -> Optional[TrainingResponse]:
        """Получение тренинга по UUID с загрузкой всех relationships"""
        training = await self.repo.get_by_uuid_with_relations(training_uuid)
        if not training:
            return None
        return TrainingResponse.model_validate(training)

    async def publish_training(self, training_uuid: UUID4) -> str:
        """
        Публикует тренинг: ставит publish=True, создаёт/обновляет публикацию.
        Возвращает публичный access_token.
        """
        training = await self.repo.get_by_uuid_with_relations(training_uuid)
        if not training:
            raise HTTPException(status_code=404, detail="Тренинг не найден")

        training.publish = True

        training_data = TrainingResponse.model_validate(training).model_dump(
            mode="json"
        )
        access_token = str(uuid.uuid4())

        await self.repo.create_or_update_publication(
            training_uuid=training.uuid,
            access_token=access_token,
            snapshot_data=training_data,
        )

        await self.session.commit()

        return access_token

    async def unpublish_training(self, training_uuid: UUID4) -> None:
        """
        Снимает тренинг с публикации: ставит publish=False,
        деактивирует все активные публикации.
        """
        training = await self.repo.get_by_uuid_with_relations(training_uuid)
        if not training:
            raise HTTPException(status_code=404, detail="Тренинг не найден")

        training.publish = False
        await self.repo.deactivate_publication(training_uuid)
        await self.session.commit()

    async def get_public_training_data(self, access_token: str):
        """
        Получает данные тренинга для прохождения (для анонимного пользователя).
        Возвращает те же данные, что и GET /training/{uuid} — по training_uuid из публикации.
        """
        publication = await self.repo.get_publication_by_token(access_token)

        if not publication:
            raise HTTPException(
                status_code=404, detail="Тренинг не найден или доступ закрыт"
            )

        await self.repo.increment_publication_views(publication.id)
        await self.session.commit()

        training = await self.repo.get_by_uuid_with_relations(publication.training_uuid)
        if not training:
            raise HTTPException(
                status_code=404, detail="Тренинг не найден или доступ закрыт"
            )

        return TrainingResponse.model_validate(training)

    async def get_trainings_by_params(
        self, skip: int = 0, limit: int = 100
    ) -> List[TrainingResponse]:
        """Получение списка тренингов с пагинацией"""
        trainings = await self.repo.get_all_with_relations(skip, limit)
        return [TrainingResponse.model_validate(t) for t in trainings]

    async def get_trainings_by_user_id(
        self, user_id: int
    ) -> List[TrainingListResponse]:
        """Получение тренингов пользователя БЕЗ шагов"""
        trainings = await self.repo.get_by_user_id(user_id)
        if not trainings:
            return None

        result = []
        for training in trainings:
            item = TrainingListResponse.model_validate(training)
            active_pub = next((p for p in training.publications if p.is_active), None)
            if active_pub:
                item.public_link = f"/training/passage/{active_pub.access_token}"
            item.steps_count = len(training.steps) if training.steps else 0
            result.append(item)
        return result

    async def patch_training(
        self, training_uuid: UUID4, training_data: TrainingUpdate
    ) -> TrainingResponse:
        """Частичное обновление тренинга и его шагов"""
        try:
            existing_training = await self.repo.get_by_uuid_with_relations(
                training_uuid
            )
            if not existing_training:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Тренинг не найден"
                )

            update_data = training_data.model_dump(
                exclude_unset=True, exclude={"steps", "tag_ids"}
            )
            if update_data:
                await self.repo.patch_training_fields(training_uuid, update_data)

            if hasattr(training_data, "tag_ids") and training_data.tag_ids is not None:
                tags_result = await self.session.execute(
                    select(Tags).where(Tags.value.in_(training_data.tag_ids))
                )
                tags = tags_result.scalars().all()
                existing_training.tags = list(tags)
                await self.session.flush()

            if hasattr(training_data, "steps") and training_data.steps is not None:
                await self.patch_training_steps(training_uuid, training_data.steps)

            await self.session.commit()

            updated_training = await self.repo.get_by_uuid_with_relations(training_uuid)
            return TrainingResponse.model_validate(updated_training)

        except HTTPException:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Непредвиденная ошибка: {str(e)}",
            )

    async def patch_training_steps(
        self,
        training_uuid: UUID4,
        steps_data: List[Union[TrainingStepCreate, TrainingStepUpdate]],
    ):
        """Частичное обновление шагов тренинга"""
        existing_steps = await self.repo.get_training_steps(training_uuid)
        existing_steps_dict = {step.id: step for step in existing_steps}

        for step_data in steps_data:
            step_id = getattr(step_data, "id", None)

            if step_id and step_id in existing_steps_dict:
                update_data = step_data.model_dump(exclude_unset=True, exclude={"id"})
                if update_data:
                    await self.repo.update_training_step(step_id, update_data)
            elif not step_id:
                step = await self.create_training_step(step_data)
                step.training_uuid = training_uuid
                await self.repo.create_training_step(step)

    async def delete_training(self, training_uuid: UUID4) -> bool:
        """Удаление тренинга"""
        success = await self.repo.delete(training_uuid)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Тренинг не найден"
            )
        return True

    async def get_training_steps(self, training_uuid: UUID4) -> List[TrainingStep]:
        """Получение шагов тренинга"""
        return await self.repo.get_training_steps(training_uuid)

    async def create_steps_from_photos(
        self, training_uuid: UUID4, photo_urls: List[str]
    ) -> List[Dict]:
        """
        Создание шагов из фотографий с вычислением размеров.
        Этот метод делегирует сохранение в репозиторий.
        """
        try:
            from utils.pg_sequences import sync_training_steps_id_sequence

            training_exists = await self.repo.check_training_exists(training_uuid)
            if not training_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Тренинг с UUID {training_uuid} не найден",
                )

            await sync_training_steps_id_sequence(self.session)

            steps_data_to_create = []

            existing_steps = await self.repo.get_training_steps(training_uuid)
            next_step_number = len(existing_steps) + 1

            for i, photo_url in enumerate(photo_urls):
                image_meta = self._get_image_dimensions(photo_url)
                sn = next_step_number + i

                steps_data_to_create.append(
                    {
                        "step_number": sn,
                        "image_url": photo_url,
                        "meta": {
                            "name": f"Шаг {sn}",
                        },
                        "photo_dimensions": {
                            "width": image_meta.get("width", 0),
                            "height": image_meta.get("height", 0),
                        },
                    }
                )

            created_steps_info = []

            for step_data in steps_data_to_create:
                new_step = TrainingStep(
                    step_number=step_data["step_number"],
                    meta=step_data["meta"],
                    training_uuid=training_uuid,
                    image_url=step_data["image_url"],
                    photo_dimensions=step_data["photo_dimensions"],
                )
                self.session.add(new_step)

                created_steps_info.append(
                    {
                        "step_number": step_data["step_number"],
                        "image_url": step_data["image_url"],
                        "dimensions": {
                            "width": step_data["photo_dimensions"]["width"],
                            "height": step_data["photo_dimensions"]["height"],
                        },
                    }
                )
            await self.session.commit()
            return created_steps_info

        except HTTPException:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка создания шагов из фотографий: {str(e)}",
            )

    def _get_image_dimensions(self, image_url: str) -> Dict[str, int]:
        """
        Загружает картинку из S3 и возвращает размеры.
        """
        try:
            img_response = requests.get(image_url, stream=True, timeout=5)
            img_response.raise_for_status()
            img = Image.open(io.BytesIO(img_response.content))
            return {
                "width": img.width,
                "height": img.height,
            }
        except Exception as e:
            logger.warning("Не удалось получить размеры для {}: {}", image_url, e)
            return {"width": 0, "height": 0}

    async def add_step(
        self, training_uuid: UUID4, step_data: TrainingStepCreate
    ) -> TrainingStepResponse:
        """Добавление одного шага к тренингу"""
        try:
            training_exists = await self.repo.check_training_exists(training_uuid)
            if not training_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Тренинг с UUID {training_uuid} не найден",
                )

            step = await self.create_training_step(step_data)
            step.training_uuid = training_uuid
            created_step = await self.repo.create_training_step(step)

            await self.session.commit()
            await self.session.refresh(created_step)

            return TrainingStepResponse.model_validate(created_step)

        except HTTPException:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка добавления шага: {str(e)}",
            )

    async def add_steps_bulk(
        self, training_uuid: UUID4, steps_data: List[TrainingStepCreate]
    ) -> List[TrainingStepResponse]:
        """Массовое добавление шагов к тренингу"""
        try:
            training_exists = await self.repo.check_training_exists(training_uuid)
            if not training_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Тренинг с UUID {training_uuid} не найден",
                )

            created_steps = []
            for step_data in steps_data:
                step = await self.create_training_step(step_data)
                step.training_uuid = training_uuid
                created_step = await self.repo.create_training_step(step)
                created_steps.append(created_step)

            await self.session.commit()

            for step in created_steps:
                await self.session.refresh(step)

            return [TrainingStepResponse.model_validate(step) for step in created_steps]

        except HTTPException:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка добавления шагов: {str(e)}",
            )

    async def update_step(
        self, training_uuid: UUID4, step_id: int, step_data: TrainingStepUpdate
    ) -> TrainingStepResponse:
        """Обновление шага по UUID тренинга и ID шага"""
        try:
            existing_step = await self.repo.get_step_by_id_and_training(
                step_id, training_uuid
            )
            if not existing_step:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Шаг {step_id} не найден в тренинге {training_uuid}",
                )

            update_data = step_data.model_dump(
                exclude_unset=True, exclude={"id", "steps"}
            )

            # Merge meta and area for partial updates (preserve existing keys)
            if "meta" in update_data and update_data["meta"] is not None:
                existing_meta = existing_step.meta or {}
                if isinstance(existing_meta, dict):
                    update_data["meta"] = {**existing_meta, **update_data["meta"]}

            area_patch = update_data.get("area") if "area" in update_data else None
            if isinstance(area_patch, dict):
                existing_area = existing_step.area or {}
                if isinstance(existing_area, dict):
                    merged_area = {**existing_area, **area_patch}
                    # Если клиент прислал area без actions, это явный переход к одиночному шагу.
                    # Иначе старые actions "призраками" остаются в прохождении.
                    if "actions" not in area_patch:
                        merged_area.pop("actions", None)
                    update_data["area"] = merged_area

            final_action_type_id = update_data.get(
                "action_type_id", existing_step.action_type_id
            )

            # keyPress: область только metaKeywords, без координат
            if final_action_type_id == ACTION_TYPE_KEY_PRESS_ID:
                area_src = update_data.get("area") or existing_step.area or {}
                update_data["area"] = {
                    "metaKeywords": (
                        area_src.get("metaKeywords")
                        if isinstance(area_src.get("metaKeywords"), list)
                        else []
                    )
                }
            elif "area" in update_data and update_data["area"] is not None:
                update_data["area"] = _sanitize_area_for_action_type(
                    update_data["area"], final_action_type_id
                )

            if update_data:
                await self.repo.update_training_step(step_id, update_data)

            await self.session.commit()

            updated_step = await self.repo.get_step_by_id(step_id)
            return TrainingStepResponse.model_validate(updated_step)

        except HTTPException:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка обновления шага: {str(e)}",
            )

    async def replace_step_screenshot(
        self,
        training_uuid: UUID4,
        step_id: int,
        creator_id: int,
        file_content: bytes,
        original_filename: str,
        s3_service: S3Service,
    ) -> TrainingStepResponse:
        if len(file_content) > 25 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл больше 25 МБ",
            )
        await self._require_training_owner(training_uuid, creator_id)
        existing_step = await self.repo.get_step_by_id_and_training(
            step_id, training_uuid
        )
        if not existing_step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Шаг не найден",
            )
        try:
            im = Image.open(io.BytesIO(file_content))
            im.load()
            w, h = im.size
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось прочитать изображение",
            )

        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
        else:
            im = im.convert("RGB")

        buf = io.BytesIO()
        im.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        object_name = s3_service.generate_unique_filename("step_edit.png")
        image_url = await s3_service.upload_file(png_bytes, object_name, training_uuid)

        return await self.update_step(
            training_uuid,
            step_id,
            TrainingStepUpdate(
                image_url=image_url,
                photo_dimensions={"width": w, "height": h},
            ),
        )

    async def get_step_screenshot_bytes(
        self,
        training_uuid: UUID4,
        step_id: int,
        creator_id: int,
        s3_service: S3Service,
    ) -> tuple[bytes, str]:
        """Байты скриншота шага из S3 (для редактора без CORS в браузере)."""
        await self._require_training_owner(training_uuid, creator_id)
        step = await self.repo.get_step_by_id_and_training(step_id, training_uuid)
        if not step or not step.image_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="У шага нет изображения",
            )
        key = _s3_object_key_from_public_url(str(step.image_url).strip())
        if not key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL изображения не совпадает с настроенным S3",
            )
        try:
            obj = s3_service.s3_client.get_object(
                Bucket=s3_service.bucket_name, Key=key
            )
        except ClientError as e:
            code = (e.response or {}).get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Файл в хранилище не найден",
                ) from e
            logger.exception("S3 get_object для скриншота шага")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Ошибка чтения из хранилища",
            ) from e

        body: bytes = obj["Body"].read()
        if len(body) > 25 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл слишком большой",
            )
        ct = obj.get("ContentType") or "image/png"
        if isinstance(ct, str) and ";" in ct:
            ct = ct.split(";")[0].strip()
        if not str(ct).startswith("image/"):
            ct = "image/png"
        return body, ct

    async def delete_step(self, training_uuid: UUID4, step_id: int) -> bool:
        """Удаление шага по UUID тренинга и ID шага"""
        try:
            existing_step = await self.repo.get_step_by_id_and_training(
                step_id, training_uuid
            )
            if not existing_step:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Шаг {step_id} не найден в тренинге {training_uuid}",
                )

            success = await self.repo.delete_training_step(step_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Шаг {step_id} не найден",
                )

            await self.session.commit()
            return True

        except HTTPException:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка удаления шага: {str(e)}",
            )

    async def delete_steps_bulk(
        self, training_uuid: UUID4, step_ids: List[int]
    ) -> Dict[str, Any]:
        """Массовое удаление шагов по UUID тренинга и списку ID"""
        try:
            deleted_count = 0
            not_found = []

            for step_id in step_ids:
                existing_step = await self.repo.get_step_by_id_and_training(
                    step_id, training_uuid
                )
                if not existing_step:
                    not_found.append(step_id)
                    continue

                success = await self.repo.delete_training_step(step_id)
                if success:
                    deleted_count += 1
                else:
                    not_found.append(step_id)

            await self.session.commit()

            return {
                "deleted": deleted_count,
                "not_found": not_found,
                "total_requested": len(step_ids),
            }

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка удаления шагов: {str(e)}",
            )

    async def reorder_steps(
        self, training_uuid: UUID4, steps_order: List[StepOrderUpdate]
    ) -> Dict[str, Any]:
        """Обновление порядка шагов в тренинге."""
        try:
            training_exists = await self.repo.check_training_exists(training_uuid)
            if not training_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Тренинг с UUID {training_uuid} не найден",
                )

            if not steps_order:
                return {"updated_count": 0, "total_requested": 0}

            step_ids_to_update = [step.id for step in steps_order]
            validated_steps_count = await self.repo.count_steps_in_training(
                training_uuid, step_ids_to_update
            )

            if validated_steps_count != len(step_ids_to_update):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Один или несколько ID шагов не принадлежат указанному тренингу.",
                )

            steps_to_update_dict = [step.model_dump() for step in steps_order]
            updated_count = await self.repo.bulk_update_step_numbers(
                steps_to_update_dict
            )

            await self.session.commit()

            return {"updated_count": updated_count, "total_requested": len(steps_order)}

        except HTTPException:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка обновления порядка шагов: {str(e)}",
            )

    async def start_async_video_processing(
        self,
        training_uuid: UUID4,
        user_id: int,
        video_file: UploadFile,
        s3_service: S3Service,
    ):
        """Загружает видео в S3, создаёт задачу и ставит в очередь Celery."""
        from models.tasks import TaskStatus, TaskType
        from repositories.tasks_repository import TasksRepository
        from schemas.tasks import TaskCreateResponse, TaskStatusEnum
        from core.redis_pubsub import publish_task_notification
        from schemas.tasks import TaskNotificationPayload
        await self._require_training_owner(training_uuid, user_id)

        if not video_file.filename:
            raise HTTPException(status_code=400, detail="Имя файла обязательно")

        if video_file.file is None:
            raise HTTPException(status_code=400, detail="Пустой файл")

        import asyncio

        object_key = s3_service.generate_task_object_key(
            user_id, video_file.filename, prefix=f"trainings/{training_uuid}/video"
        )
        content_type = video_file.content_type or "video/mp4"

        # Потоковая загрузка файла в S3 без чтения всего видео в память web-процесса.
        try:
            await asyncio.to_thread(video_file.file.seek, 0)
            file_url = await asyncio.to_thread(
                s3_service.upload_fileobj_sync, video_file.file, object_key, content_type
            )
        finally:
            await video_file.close()

        tasks_repo = TasksRepository(self.session)
        task = await tasks_repo.create(
            user_id=user_id,
            file_url=file_url,
            task_type=TaskType.VIDEO_PROCESSING.value,
            status=TaskStatus.PENDING.value,
            progress=0,
            original_filename=video_file.filename,
            training_uuid=training_uuid,
        )

        # Ставим задачу в очередь без импорта worker-модулей в web-процесс.
        from core.task_queue import enqueue_process_training_video

        await asyncio.to_thread(enqueue_process_training_video, str(task.id))

        await asyncio.to_thread(
            publish_task_notification,
            user_id,
            TaskNotificationPayload(
                type="task_update",
                task_id=str(task.id),
                status=TaskStatus.PENDING.value,
                progress=0,
                message="Видео принято в обработку. Можно продолжать работу — шаги появятся автоматически.",
                training_uuid=str(training_uuid),
                task_type=TaskType.VIDEO_PROCESSING.value,
            ),
        )

        return TaskCreateResponse(
            task_id=task.id,
            status=TaskStatusEnum.PENDING,
            message="Видео принято в обработку",
            training_uuid=training_uuid,
        )

    async def add_steps_from_video(
        self,
        training_uuid: UUID4,
        video_file: UploadFile,
        video_ai_service: VideoAIService,
        s3_service: S3Service,
        creator_id: Optional[int] = None,
    ) -> List[Dict]:
        """
        Синхронная обработка (legacy). Предпочтительно start_async_video_processing.
        """
        try:
            if creator_id is not None:
                await self._require_training_owner(training_uuid, creator_id)
            else:
                training_exists = await self.repo.check_training_exists(training_uuid)
                if not training_exists:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Тренинг с UUID {training_uuid} не найден",
                    )

            ai_steps = await video_ai_service.analyze_video(video_file)
            return await self.create_steps_from_ai_steps(
                training_uuid=training_uuid,
                ai_steps=ai_steps,
                s3_service=s3_service,
                creator_id=creator_id,
            )
        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.exception("Ошибка AI-анализа видео и создания шагов")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка AI-анализа видео и создания шагов: {str(e)}",
            )

    async def create_steps_from_ai_steps(
        self,
        training_uuid: UUID4,
        ai_steps: list,
        s3_service: S3Service,
        creator_id: Optional[int] = None,
    ) -> List[Dict]:
        """Создаёт шаги тренинга из результата AI-анализа видео."""
        import asyncio

        if creator_id is not None:
            await self._require_training_owner(training_uuid, creator_id)
        elif not await self.repo.check_training_exists(training_uuid):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Тренинг с UUID {training_uuid} не найден",
            )

        if not ai_steps:
            return []

        from utils.pg_sequences import sync_training_steps_id_sequence

        await sync_training_steps_id_sequence(self.session)

        try:
            DEFAULT_ACTION_TYPE_ID = 1

            existing_steps = await self.repo.get_training_steps(training_uuid)
            next_step_number = len(existing_steps) + 1

            created_steps_info = []

            for i, step_data in enumerate(ai_steps):
                filename = f"video_ai_step_{i + 1:03d}.png"
                object_name = s3_service.generate_unique_filename(filename)

                # Загружаем в S3 в отдельном потоке
                image_url = await asyncio.to_thread(
                    s3_service.upload_bytes_sync,
                    step_data.frame_bytes,
                    object_name,
                    "image/png",
                )
                image_url = (
                    f"{s3_service.endpoint_url}/{s3_service.bucket_name}/{object_name}"
                )

                image_url_after: Optional[str] = None
                if step_data.after_frame_bytes:
                    after_name = s3_service.generate_unique_filename(
                        f"video_ai_step_{i + 1:03d}_after.png"
                    )
                    await asyncio.to_thread(
                        s3_service.upload_bytes_sync,
                        step_data.after_frame_bytes,
                        after_name,
                        "image/png",
                    )
                    image_url_after = f"{s3_service.endpoint_url}/{s3_service.bucket_name}/{after_name}"

                bbox = step_data.bbox
                fw = float(step_data.frame_width or 1)
                fh = float(step_data.frame_height or 1)
                b0, b1, b2, b3 = [float(v) for v in bbox]
                mx = max(b0, b1, b2, b3)

                # Универсальная интерпретация bbox:
                # - 0..1: нормализованный
                # - 0..100: проценты
                # - 0..1000: тысячные доли (legacy)
                # - иначе: пиксели
                if mx <= 1.0:
                    sx = 1.0
                elif mx <= 100.0:
                    sx = 0.01
                elif mx <= 1000.0:
                    sx = 0.001
                else:
                    sx = None

                if sx is not None:
                    x1 = max(0.0, min(1.0, b0 * sx))
                    y1 = max(0.0, min(1.0, b1 * sx))
                    x2 = max(0.0, min(1.0, b2 * sx))
                    y2 = max(0.0, min(1.0, b3 * sx))
                    x_min, x_max = min(x1, x2), max(x1, x2)
                    y_min, y_max = min(y1, y2), max(y1, y2)
                    area: Dict[str, Any] = {
                        "x": x_min * fw,
                        "y": y_min * fh,
                        "width": max(1.0, (x_max - x_min) * fw),
                        "height": max(1.0, (y_max - y_min) * fh),
                    }
                else:
                    x1 = max(0.0, min(fw, b0))
                    y1 = max(0.0, min(fh, b1))
                    x2 = max(0.0, min(fw, b2))
                    y2 = max(0.0, min(fh, b3))
                    x_min, x_max = min(x1, x2), max(x1, x2)
                    y_min, y_max = min(y1, y2), max(y1, y2)
                    area = {
                        "x": x_min,
                        "y": y_min,
                        "width": max(1.0, x_max - x_min),
                        "height": max(1.0, y_max - y_min),
                    }

                # Жёсткая защита от аномалий размера (слишком крупная/слишком мелкая область)
                max_w = fw * 0.7
                max_h = fh * 0.7
                area["width"] = max(1.0, min(float(area["width"]), max_w))
                area["height"] = max(1.0, min(float(area["height"]), max_h))

                action_key = (step_data.action_type_key or "left_click").lower()
                action_type_id = ACTION_TYPE_KEY_TO_ID.get(
                    action_key, DEFAULT_ACTION_TYPE_ID
                )

                if action_key == "text_input" and step_data.expected_text:
                    area["metaText"] = step_data.expected_text
                if action_key == "key_chord" and step_data.key_chord:
                    area["metaKeywords"] = list(step_data.key_chord)

                step_meta: Dict[str, Any] = {
                    "name": step_data.step_title,
                    "source": "video_ai",
                    "ai_timecode": step_data.timecode,
                    "ai_timecode_before": step_data.timecode_before
                    or step_data.timecode,
                    "ai_timecode_after": step_data.timecode_after,
                }
                if image_url_after:
                    step_meta["image_url_after"] = image_url_after

                new_step = TrainingStep(
                    step_number=next_step_number + i,
                    meta=step_meta,
                    training_uuid=training_uuid,
                    image_url=image_url,
                    photo_dimensions={
                        "width": step_data.frame_width,
                        "height": step_data.frame_height,
                    },
                    area=area,
                    action_type_id=action_type_id,
                    annotation=step_data.instruction_md,
                )
                self.session.add(new_step)
                created_steps_info.append(
                    {
                        "step_number": next_step_number + i,
                        "image_url": image_url,
                        "image_url_after": image_url_after,
                        "name": step_data.step_title,
                        "timecode": step_data.timecode,
                        "timecode_before": step_data.timecode_before,
                        "timecode_after": step_data.timecode_after,
                        "area": area,
                        "action_type_id": action_type_id,
                        "action_type_key": action_key,
                        "dimensions": {
                            "width": step_data.frame_width,
                            "height": step_data.frame_height,
                        },
                    }
                )

            await self.session.commit()

            return created_steps_info

        except HTTPException:
            raise
        except IntegrityError as exc:
            await self.session.rollback()
            err = str(getattr(exc, "orig", exc))
            if "training_steps_pkey" in err or "UniqueViolation" in err:
                await sync_training_steps_id_sequence(self.session)
                await self.session.commit()
                logger.error(
                    "Конфликт id training_steps после синхронизации sequence: {}",
                    err,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "Ошибка создания шагов: конфликт идентификаторов в базе данных. "
                        "Обновите backend (alembic upgrade head) и повторите загрузку видео."
                    ),
                )
            raise
        except Exception as e:
            await self.session.rollback()
            logger.exception("Ошибка создания шагов из AI-анализа")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка создания шагов: {str(e)}",
            )

    async def _require_training_owner(
        self, training_uuid: UUID4, creator_id: int
    ) -> Training:
        training = await self.repo.get_by_uuid(training_uuid)
        if not training or training.creator_id != creator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа к этому тренингу",
            )
        return training

    async def start_public_passage_attempt(self, access_token: str) -> dict:
        publication = await self.repo.get_publication_by_token(access_token)
        if not publication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Тренинг не найден или доступ закрыт",
            )
        att = await self.repo.create_passage_attempt(publication.id)
        await self.session.commit()
        return {"attempt_id": att.id}

    async def complete_public_passage_attempt(
        self, access_token: str, body: PassageCompleteRequest
    ) -> dict:
        publication = await self.repo.get_publication_by_token(access_token)
        if not publication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Тренинг не найден или доступ закрыт",
            )
        ok = await self.repo.complete_passage_attempt(
            body.attempt_id,
            publication.id,
            body.is_completed,
            body.duration_seconds,
            body.wrong_attempts_total,
        )
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Попытка не найдена или уже завершена",
            )
        await self.session.commit()
        return {"success": True}

    async def get_passage_analytics_for_creator(
        self, training_uuid: UUID4, creator_id: int
    ) -> PassageAnalyticsResponse:
        await self._require_training_owner(training_uuid, creator_id)
        stats = await self.repo.get_passage_stats_for_training(training_uuid)
        return PassageAnalyticsResponse(**stats)

    async def get_passage_history_for_creator(
        self,
        training_uuid: UUID4,
        creator_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> List[PassageHistoryItemResponse]:
        await self._require_training_owner(training_uuid, creator_id)
        rows = await self.repo.list_passage_attempts_for_training(
            training_uuid, skip=skip, limit=min(limit, 100)
        )
        return [PassageHistoryItemResponse.model_validate(r) for r in rows]

    async def add_steps_from_pdf(
        self,
        training_uuid: UUID4,
        pdf_bytes: bytes,
        pdf_ai_service: PdfAiService,
        s3_service: S3Service,
    ) -> List[Dict]:
        """
        Обрабатывает PDF-инструкцию через VLM-модель:
        1. Каждая страница рендерится в PNG
        2. VLM определяет кликабельную область по тексту страницы
        3. PNG загружается в S3
        4. Создаётся шаг тренинга с областью, описанием и скрином
        """
        try:
            training_exists = await self.repo.check_training_exists(training_uuid)
            if not training_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Тренинг с UUID {training_uuid} не найден",
                )

            # Анализируем PDF через VLM
            pdf_steps = await pdf_ai_service.analyze_pdf(pdf_bytes)

            if not pdf_steps:
                return []

            DEFAULT_ACTION_TYPE_ID = 1

            existing_steps = await self.repo.get_training_steps(training_uuid)
            next_step_number = len(existing_steps) + 1

            created_steps_info = []

            # Параллельная загрузка PNG страниц в S3
            import asyncio
            async def _upload_step_image(idx, data):
                filename = f"pdf_step_{data.page_number:03d}.png"
                object_name = s3_service.generate_unique_filename(filename)
                url = await s3_service.upload_file(data.page_bytes, object_name, training_uuid)
                return idx, url

            upload_tasks = [_upload_step_image(i, step) for i, step in enumerate(pdf_steps)]
            upload_results = await asyncio.gather(*upload_tasks)
            upload_results.sort(key=lambda x: x[0])
            image_urls = [res[1] for res in upload_results]

            for i, step_data in enumerate(pdf_steps):
                image_url = image_urls[i]

                bbox = step_data.bbox
                # bbox уже нормализован 0..1 в PdfAiService
                x1, y1, x2, y2 = bbox
                x_min, x_max = min(x1, x2), max(x1, x2)
                y_min, y_max = min(y1, y2), max(y1, y2)
                area: Dict[str, Any] = {
                    "x": x_min * step_data.page_width,
                    "y": y_min * step_data.page_height,
                    "width": max(1.0, (x_max - x_min) * step_data.page_width),
                    "height": max(1.0, (y_max - y_min) * step_data.page_height),
                }

                action_key = (step_data.action_type_key or "left_click").lower()
                action_type_id = ACTION_TYPE_KEY_TO_ID.get(
                    action_key, DEFAULT_ACTION_TYPE_ID
                )

                if action_key == "text_input" and step_data.expected_text:
                    area["metaText"] = step_data.expected_text
                if action_key == "key_chord" and step_data.key_chord:
                    area["metaKeywords"] = list(step_data.key_chord)

                step_meta: Dict[str, Any] = {
                    "name": step_data.step_title,
                    "source": "pdf_ai",
                    "pdf_page": step_data.page_number,
                }

                new_step = TrainingStep(
                    step_number=next_step_number + i,
                    meta=step_meta,
                    training_uuid=training_uuid,
                    image_url=image_url,
                    photo_dimensions={
                        "width": step_data.page_width,
                        "height": step_data.page_height,
                    },
                    area=area,
                    action_type_id=action_type_id,
                    annotation=step_data.instruction_md,
                )
                self.session.add(new_step)

                created_steps_info.append(
                    {
                        "step_number": next_step_number + i,
                        "pdf_page": step_data.page_number,
                        "image_url": image_url,
                        "name": step_data.step_title,
                        "area": area,
                        "action_type_id": action_type_id,
                        "action_type_key": action_key,
                        "dimensions": {
                            "width": step_data.page_width,
                            "height": step_data.page_height,
                        },
                    }
                )

            await self.session.commit()
            return created_steps_info

        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка AI-анализа PDF и создания шагов: {str(e)}",
            )
