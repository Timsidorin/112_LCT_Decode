from typing import Optional

from fastapi import BackgroundTasks, HTTPException, status
from pydantic import EmailStr

from core.config import configs
from models.users import User as UserModel
from repositories.users_repository import UserRepository
from schemas.users import User, UserLogin, UserRegister, UserResponse
from utils.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


class UserService:
    def __init__(self, repo: UserRepository):
        self.user_repo = repo

    async def register(self, user_data: UserRegister) -> bool:
        return await self.user_repo.add_user(user_data)

    async def authenticate(self, email: EmailStr, password: str):
        user = await self.user_repo.find_one_or_none(email=email)
        if (
            not user
            or not user.password
            or not verify_password(
                plain_password=password, hashed_password=user.password
            )
        ):
            return None
        return user

    async def login(self, credential: UserLogin) -> Optional[str]:
        # Используем authenticate_user для проверки email и пароля
        user = await self.authenticate(
            email=credential.username, password=credential.password
        )
        if not user:
            return None

        access_token = create_access_token(
            data={"sub": user.email},
        )
        return access_token

    async def get_current_user(self, token: str) -> UserResponse:
        payload = decode_access_token(token=token)
        email: str = payload.get("sub")

        user = await self.user_repo.find_one_or_none(email=email)
        if user is None:
            return None
        return UserResponse.model_validate(user)

    async def get_or_create_yandex_user(
        self,
        yandex_id: str,
        email_from_yandex: Optional[str],
        first_name: str,
        last_name: str,
        photo: Optional[str],
    ) -> UserModel:
        existing = await self.user_repo.find_by_yandex_id(yandex_id)
        if existing:
            u = await self.user_repo.update_user(
                existing.id,
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "photo": photo,
                },
            )
            if u:
                return u
            return await self.user_repo.get_by_id(existing.id)

        if email_from_yandex:
            by_email = await self.user_repo.find_one_or_none(email_from_yandex)
            if by_email:
                if by_email.yandex_id is None or by_email.yandex_id == yandex_id:
                    u2 = await self.user_repo.update_user(
                        by_email.id,
                        {
                            "yandex_id": yandex_id,
                            "first_name": first_name,
                            "last_name": last_name,
                            "photo": photo or by_email.photo,
                        },
                    )
                    if u2:
                        return u2
                    return await self.user_repo.get_by_id(by_email.id)

        new_email = f"yandex_{yandex_id}@yandex.oauth.local"
        if email_from_yandex and not await self.user_repo.find_one_or_none(
            email_from_yandex
        ):
            new_email = email_from_yandex

        db_user = UserModel(
            email=new_email,
            yandex_id=yandex_id,
            password=None,
            phone_number=None,
            first_name=first_name,
            last_name=last_name,
            photo=photo,
        )
        self.user_repo.session.add(db_user)
        await self.user_repo.session.commit()
        await self.user_repo.session.refresh(db_user)
        return db_user
