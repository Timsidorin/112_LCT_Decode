from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Body, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from starlette import status

from core.config import configs
from depends import get_user_service, oauth2_scheme
from schemas.users import UserLogin, UserRegister, UserResponse
from services.user_service import UserService
from utils.security import create_access_token, decode_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/register", name="регистрация пользователя")
async def register_user(
    user_data: UserRegister,
    user_service: UserService = Depends(get_user_service),
) -> None:
    if await user_service.register(user_data):
        raise HTTPException(
            status_code=200,
            detail="Вы успешно зарегистрированы! На ваш email отправлено письмо.",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует!",
        )


@router.post("/login", name="Логин")
async def login_user(
    username: Optional[str] = Form(default=None),
    password: Optional[str] = Form(default=None),
    user_data: Optional[UserLogin] = Body(default=None),
    user_service: UserService = Depends(get_user_service),
) -> dict:
    if user_data:
        final_user_data = user_data
    elif username and password:
        final_user_data = UserLogin(username=username, password=password)
    else:
        raise HTTPException(
            status_code=400,
            detail="Некорректные данные",
        )
    access_token = await user_service.login(final_user_data)
    if access_token is None:
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me/", name="Получение данных текущего пользователя")
async def get_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    current_user = await user_service.get_current_user(token)
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось загрузить пользователя",
        )
    return current_user


