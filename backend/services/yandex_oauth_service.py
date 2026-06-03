"""OAuth 2.0 авторизация через Яндекс ID (oauth.yandex.ru)."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from core.config import configs

YANDEX_AUTH = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN = "https://oauth.yandex.ru/token"
YANDEX_INFO = "https://login.yandex.ru/info"
DEFAULT_SCOPES = "login:info login:email login:avatar"


@dataclass
class YandexProfile:
    yandex_id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    photo: Optional[str] = None


def build_yandex_authorize_url(*, state: str) -> str:
    client_id = (configs.YANDEX_CLIENT_ID or "").strip()
    redirect_uri = (configs.YANDEX_REDIRECT_URI or "").strip()
    if not client_id or not redirect_uri:
        raise ValueError("Yandex OAuth is not configured")
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": DEFAULT_SCOPES,
        "state": state,
        "force_confirm": "yes",
    }
    return f"{YANDEX_AUTH}?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> str:
    client_id = (configs.YANDEX_CLIENT_ID or "").strip()
    client_secret = (configs.YANDEX_CLIENT_SECRET or "").strip()
    redirect_uri = (configs.YANDEX_REDIRECT_URI or "").strip()
    if not client_id or not client_secret:
        raise ValueError("Yandex OAuth is not configured")
    if not redirect_uri:
        raise ValueError("YANDEX_REDIRECT_URI is not configured")

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = {
        "grant_type": "authorization_code",
        "code": code.strip(),
        "redirect_uri": redirect_uri,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {basic}",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(YANDEX_TOKEN, data=body, headers=headers)
    try:
        data: dict[str, Any] = r.json()
    except Exception as exc:
        raise ValueError(
            f"yandex token: HTTP {r.status_code}, body: {r.text[:400]!r}"
        ) from exc

    if r.status_code >= 400:
        err = data.get("error_description") or data.get("error") or r.text[:300]
        raise ValueError(f"yandex token HTTP {r.status_code}: {err}")

    if "error" in data:
        err = data.get("error_description") or data.get("error", "token_error")
        raise ValueError(str(err))

    access_token = data.get("access_token")
    if not access_token:
        raise ValueError("Invalid token response from Yandex")
    return str(access_token)


def _avatar_from_info(info: dict[str, Any]) -> Optional[str]:
    if info.get("is_avatar_empty") is True:
        return None
    url = info.get("default_avatar")
    if isinstance(url, str) and url.startswith("http"):
        return url
    aid = info.get("default_avatar_id")
    if isinstance(aid, str) and aid.strip():
        return f"https://avatars.yandex.net/get-yapic/{aid.strip()}/islands-200"
    return None


def _names_from_info(info: dict[str, Any]) -> tuple[str, str]:
    rn = info.get("real_name")
    if isinstance(rn, dict):
        fn = (rn.get("first_name") or "").strip()
        ln = (rn.get("last_name") or "").strip()
        if fn or ln:
            return fn or "Пользователь", ln or "Яндекс"
    if isinstance(rn, str) and rn.strip():
        parts = rn.strip().split(None, 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return parts[0], "Яндекс"
    dn = (info.get("display_name") or "").strip()
    if dn:
        parts = dn.split(None, 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return parts[0], "Яндекс"
    login = (info.get("login") or "").strip() or "user"
    return login, "Яндекс"


def _email_from_info(info: dict[str, Any]) -> Optional[str]:
    de = info.get("default_email")
    if isinstance(de, str) and de.strip():
        return de.strip()
    emails = info.get("emails")
    if isinstance(emails, list) and emails:
        e0 = emails[0]
        if isinstance(e0, str) and e0.strip():
            return e0.strip()
    return None


async def fetch_yandex_profile(access_token: str) -> YandexProfile:
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(
            YANDEX_INFO,
            params={"format": "json"},
            headers={"Authorization": f"OAuth {access_token}"},
        )
        r.raise_for_status()
        info: dict[str, Any] = r.json()
    uid = info.get("id")
    if uid is None:
        raise ValueError("Yandex /info: missing id")
    yandex_id = str(uid).strip()
    if not yandex_id:
        raise ValueError("Yandex /info: empty id")
    first_name, last_name = _names_from_info(info)
    if not first_name:
        first_name = "Пользователь"
    if not last_name:
        last_name = "Яндекс"
    return YandexProfile(
        yandex_id=yandex_id,
        first_name=first_name,
        last_name=last_name,
        email=_email_from_info(info),
        photo=_avatar_from_info(info),
    )
